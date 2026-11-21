"""工程评议的数值绑定、身份一致、证据引用及段落完整性。"""

from copy import deepcopy
import json

import pytest

from core.report_review import (
    parse_engineering_review, prepare_review_payload, render_engineering_review, review_engineering_content,
    validate_engineering_review, validate_review_check,
)


def payload():
    return prepare_review_payload(
        [{"candidate_id": "C1", "metric": "capacity", "value": 12.34567, "unit": "MPa"},
         {"candidate_id": None, "metric": "scope", "value": "未验证制造与试验", "unit": ""}],
        {"selected": {"candidate_id": "C1"}}, lambda fact: str(fact["value"]) + " " + fact["unit"],
        context={"results": [{"candidate_id": "C1", "session_candidate_id": "TMP_7"}]},
        evidence=[{"source_label": "S1"}], required_metrics=[("C1", "capacity")],
    )


def answer():
    return {"recommendation_candidate_id": "C1",
            "assessment": "C1 的容量为{{C1.capacity}}，推荐限于该载荷与边界条件下的数值结果。",
            "tradeoffs": ["目前仅有该方案的完整求解容量{{C1.capacity}}，不足以证明其他构型具有更低重量。"],
            "verification": ["当前证据范围为{{TASK.scope}}，应先核查实际装配边界能否实现模型约束。"]}


def test_natural_review_preserves_original_facts_and_resolves_inline_values():
    context, original = payload(), answer()
    before = deepcopy(context)
    accepted = validate_engineering_review(json.dumps(original, ensure_ascii=False), context)
    text = render_engineering_review(accepted, context)
    assert "12.34567 MPa" in text and "{{" not in text
    assert accepted["paragraph_refs"] == [["C1.capacity"], ["C1.capacity"], ["TASK.scope"]]
    assert context == before
    assert accepted["assessment"] == original["assessment"]
    original["verification"].extend(["针对{{C1.capacity}}补充网格对照。", "按{{TASK.scope}}核对连接假设。"])
    assert len(validate_engineering_review(json.dumps(original), context)["verification"]) == 3


@pytest.mark.parametrize("mutation", [
    "unknown_fact", "unknown_source", "unbound_number", "unknown_candidate", "missing_reference",
    "wrong_recommendation", "extra_field", "empty_verification", "bad_tradeoff_type",
    "duplicate_paragraph", "partial_token", "injected_heading", "missing_decision_fact",
])
def test_invalid_review_is_not_rewritten_or_silently_accepted(mutation):
    context, response = payload(), answer()
    if mutation == "unknown_fact":
        response["assessment"] += "{{F99}}"
    elif mutation == "unknown_source":
        response["verification"][0] += "{{E9}}"
    elif mutation == "unbound_number":
        response["assessment"] += "制造公差取 0.3 mm。"
    elif mutation == "unknown_candidate":
        response["assessment"] += "推荐 C99。"
    elif mutation == "missing_reference":
        response["tradeoffs"][0] = "只需要采用更加先进的制造工艺就可以通过。"
    elif mutation == "wrong_recommendation":
        response["recommendation_candidate_id"] = "C2"
    elif mutation == "extra_field":
        response["capacity"] = 999
    elif mutation == "empty_verification":
        response["verification"] = []
    elif mutation == "bad_tradeoff_type":
        response["tradeoffs"] = "不是段落列表"
    elif mutation == "duplicate_paragraph":
        response["tradeoffs"] = [response["assessment"]]
    elif mutation == "partial_token":
        response["assessment"] += "{{F"
    elif mutation == "injected_heading":
        response["assessment"] += "\n# 无依据结论"
    else:
        response["assessment"] = "证据只说明{{TASK.scope}}，没有交代支持当前推荐的校核结果。"
    before = deepcopy(response)
    with pytest.raises(ValueError) as error:
        validate_engineering_review(json.dumps(response, ensure_ascii=False), context)
    if mutation == "missing_reference":
        assert "tradeoffs[0]" in str(error.value)
    assert response == before


def test_duplicate_json_fields_and_duplicate_input_facts_are_rejected():
    response = json.dumps(answer()).replace('"assessment":', '"assessment": "重复", "assessment":')
    with pytest.raises(ValueError, match="重复"):
        validate_engineering_review(response, payload())
    fact = {"candidate_id": "C1", "metric": "capacity", "value": 1}
    with pytest.raises(ValueError, match="重复"):
        prepare_review_payload([fact, dict(fact)], {"selected": None}, str, context={})


def test_no_recommendation_and_evidence_citation_remain_explicit():
    context = payload()
    context["recommendation"]["selected"] = None
    response = answer()
    response["recommendation_candidate_id"] = None
    response["verification"][0] += "文献中的验证思路见{{E1}}，其数值不是本模型的结果。"
    accepted = validate_engineering_review(json.dumps(response), context)
    assert "[E1]" in render_engineering_review(accepted, context)
    assert accepted["recommendation_candidate_id"] is None


def test_content_review_keeps_issues_and_only_accepts_rechecked_revision():
    context, audit = payload(), {}
    draft = validate_engineering_review(json.dumps(answer()), context)
    issue = {"quote": "C1 的容量为12.34567 MPa", "issue": "候选对应关系需要更正", "fact_refs": ["C1.capacity"]}
    responses = [json.dumps({"accepted": False, "issues": [issue]}),
                 json.dumps(answer()), json.dumps({"accepted": True, "issues": []})]
    seen = []
    def chat(system, user):
        seen.append(json.loads(user))
        return responses.pop(0)
    accepted = review_engineering_content(chat, draft, context, audit)
    assert accepted["recommendation_candidate_id"] == "C1"
    assert [item["accepted"] for item in audit["content_checks"]] == [False, True]
    assert seen[1]["review_issues"] == [issue]
    assert set(seen[1]["draft"]) == set(answer())
    assert "response_schema" not in seen[0]["evidence"]
    assert seen[0]["evidence"]["facts"] == context["facts"]
    assert seen[0]["evidence"]["candidate_bindings"] == [{"candidate_id": "C1", "session_candidate_id": "TMP_7"}]
    assert not responses


def test_content_review_stops_after_a_failed_directed_revision():
    context, audit = payload(), {}
    draft = validate_engineering_review(json.dumps(answer()), context)
    issue = {"quote": "C1 的容量为12.34567 MPa", "issue": "把余量当成特征值", "fact_refs": ["C1.capacity"]}
    responses = [json.dumps({"accepted": False, "issues": [issue]}),
                 json.dumps(answer()), json.dumps({"accepted": False, "issues": [{**issue, "issue": "缺少方案对照"}]})]
    with pytest.raises(ValueError, match="缺少方案对照"):
        review_engineering_content(lambda *_: responses.pop(0), draft, context, audit)
    assert len(audit["content_checks"]) == 2 and not responses


@pytest.mark.parametrize("response", ["{}", '{"accepted":1,"issues":[]}',
    '{"accepted":true,"issues":["仍有错误"]}', '{"accepted":false,"issues":[]}', "无法核查"])
def test_invalid_content_check_does_not_count_as_semantic_acceptance(response):
    with pytest.raises(ValueError):
        validate_review_check(response, payload(), "报告原文")


def test_content_check_rejects_a_fabricated_report_quote():
    result = {"accepted": False, "issues": [{"quote": "报告没有写过的话", "issue": "错误", "fact_refs": ["C1.capacity"]}]}
    with pytest.raises(ValueError, match="原句"):
        validate_review_check(json.dumps(result), payload(), "实际报告")


def test_invalid_content_check_response_is_retained_for_diagnosis():
    context, audit = payload(), {}
    draft = validate_engineering_review(json.dumps(answer()), context)
    with pytest.raises(ValueError):
        review_engineering_content(lambda *_: "无法核查", draft, context, audit)
    assert audit["content_checks"] == [{"raw_response": "无法核查"}]


def test_contract_repair_is_bounded_and_keeps_original_error():
    context, audit = payload(), {}
    response = answer()
    response["unused"] = None
    accepted = parse_engineering_review(lambda *_: json.dumps(answer()), json.dumps(response), context, audit)
    assert accepted["recommendation_candidate_id"] == "C1"
    assert audit["contract_issue"] and audit["contract_repair_response"]
    with pytest.raises(ValueError):
        parse_engineering_review(lambda *_: json.dumps(response), json.dumps(response), context, {})
    response = answer()
    response["assessment"] = response["assessment"].replace("{{C1.capacity}}", "{{C1.capacity}} MPa")
    with pytest.raises(ValueError) as error:
        validate_engineering_review(json.dumps(response), context)
    assert "C1.capacity" in str(error.value) and "MPa" in str(error.value)
    assert parse_engineering_review(lambda *_: json.dumps(answer()), json.dumps(response), context, {})["assessment"] == answer()["assessment"]


def test_single_comparable_result_cannot_produce_a_comparative_tradeoff():
    context = payload()
    context["comparison_count"] = 1
    with pytest.raises(ValueError, match="方案不足"):
        validate_engineering_review(json.dumps(answer()), context)


def test_unconfirmed_metric_is_retained_as_missing_evidence_not_a_renderable_value():
    missing = {"candidate_id": "C1", "metric": "local_mode", "value": None, "unit": "1"}
    context = prepare_review_payload([*payload()["facts"], missing], payload()["recommendation"],
                                     lambda fact: str(fact["value"]), context={})
    assert context["unavailable_facts"] == [missing]
    assert all(fact["ref"] != "C1.local_mode" for fact in context["facts"])
    response = answer()
    response["verification"][0] = "局部模态尚未识别，{{C1.local_mode}}不能用来确认局部失效。"
    with pytest.raises(ValueError, match="未知引用") as error:
        validate_engineering_review(json.dumps(response), context)
    assert "C1.local_mode" in str(error.value)
    check = {"accepted": False, "issues": [{"quote": "已确认局部失效", "issue": "局部模态没有计算证据",
                                            "fact_refs": ["C1.local_mode"]}]}
    assert validate_review_check(json.dumps(check), context, "已确认局部失效") == check


@pytest.mark.parametrize("section", ["tradeoffs", "verification"])
def test_review_sections_reject_non_text_paragraphs(section):
    response = answer()
    response[section] = [None]
    with pytest.raises(ValueError):
        validate_engineering_review(json.dumps(response), payload())
