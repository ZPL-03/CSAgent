"""多智能体职责契约。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentContract:
    """运行时智能体职责、输入输出和失败边界。"""

    node_name: str
    label: str
    runtime_agent: str
    implementation: str
    tool_name: str
    responsibility: str
    input_contract: str
    output_contract: str
    llm_policy: str
    failure_policy: str


AGENT_CONTRACTS: tuple[AgentContract, ...] = (
    AgentContract(
        node_name="parse_task",
        label="任务解析",
        runtime_agent="RequirementAgent",
        implementation="core.task_parser.TaskParser",
        tool_name="parse_task",
        responsibility="把自然语言需求转换为结构化任务契约和用户已给事实。",
        input_contract="自然语言需求、可选覆盖参数。",
        output_contract="task 字典；包含候选池总数、初筛数量、工况、边界、目标和几何参考或固定约束。",
        llm_policy="不调用 LLM。",
        failure_policy="缺少候选池总数或初筛数量时直接失败，主流程不启动。",
    ),
    AgentContract(
        node_name="generate_candidates",
        label="候选生成",
        runtime_agent="CandidateStrategyAgent",
        implementation="agents.candidate_gen.CandidateGenAgent",
        tool_name="generate_candidates",
        responsibility="按 LLM、案例迁移和 DOE 三路生成候选池，并完成字段校验、规则检查和结构去重。",
        input_contract="task 字典。",
        output_contract="candidates 列表；候选编号为 TMP_N，display_name 与 candidate_id 一致。",
        llm_policy="仅 LLM 来源候选调用 LLM；主模型优先，失败后回退，输出经自然语言表格解析后才进入候选池。",
        failure_policy="LLM 输出不合规或案例不足不阻断流程，由 DOE 在参数域内补足候选池数量。",
    ),
    AgentContract(
        node_name="screen_candidates",
        label="代理初筛",
        runtime_agent="SurrogateAgent",
        implementation="agents.screener.ScreenerAgent",
        tool_name="screen_candidates",
        responsibility="计算 ASME RD-1172 线性屈曲压力和 PBIPF 极限压力，按评分公式排序。",
        input_contract="task 字典、candidates 列表。",
        output_contract="screened_candidates 列表；数量由当前任务 top_k 和候选池实际数量共同确定。",
        llm_policy="不调用 LLM。",
        failure_policy="候选缺少必要工程字段时按规则诊断剔除或抛出确定性错误，不使用 LLM 补数。",
    ),
    AgentContract(
        node_name="evaluate_candidates",
        label="有限元校核",
        runtime_agent="FEMExecutionAgent",
        implementation="agents.fem_agent.FEMAgent",
        tool_name="evaluate_candidates",
        responsibility="将会话候选晋级为正式 C_N 输入，执行 Abaqus 两阶段真实有限元校核并记录作业队列。",
        input_contract="task 字典、evaluated_candidates 列表。",
        output_contract="results 列表、fem_designs 列表；结果保留 session_candidate_id 用于回溯 TMP_N。",
        llm_policy="不调用 LLM。",
        failure_policy="Abaqus 不可用或求解失败时返回诊断结果，不伪造通过；作业队列记录失败原因。",
    ),
    AgentContract(
        node_name="persist_knowledge",
        label="知识回流",
        runtime_agent="KnowledgeMemoryAgent",
        implementation="agents.knowledge_agent.KnowledgeAgent",
        tool_name="persist_knowledge",
        responsibility="把有限元结果、正式候选和任务契约写入案例库、案例记忆和代理公式校准数据。",
        input_contract="task 字典、fem_designs 列表、results 列表。",
        output_contract="knowledge_updates 列表；包含 case_id、存储状态和校准摘要。",
        llm_policy="不调用 LLM。",
        failure_policy="单个案例回流失败会写入失败摘要和事件诊断，不修改有限元结果本身。",
    ),
    AgentContract(
        node_name="generate_report",
        label="报告生成",
        runtime_agent="ReportAgent",
        implementation="agents.report_gen.ReportGenAgent",
        tool_name="generate_report",
        responsibility="基于结构化任务、候选和有限元结果生成 Markdown/PDF 报告。",
        input_contract="task 字典、results 列表、candidates 列表。",
        output_contract="report 字典；包含 Markdown/PDF 路径、正文和 LLM 工程解释使用状态。",
        llm_policy="只在工程解释和制造建议中受控调用 LLM；数值、排序和结论由结构化数据确定。",
        failure_policy="LLM 解释失败时退回确定性解释；报告文件生成失败时写入节点失败事件。",
    ),
)


def list_agent_contracts() -> list[AgentContract]:
    """返回运行时智能体契约。"""

    return list(AGENT_CONTRACTS)


def contract_by_node() -> dict[str, AgentContract]:
    """按状态图节点索引智能体契约。"""

    return {contract.node_name: contract for contract in AGENT_CONTRACTS}
