# CSDM_cph

CSDM_cph 是复合材料外压圆柱耐压壳智能设计系统。主流程为：

自然语言需求 -> 用户事实抽取 -> LLM 候选提案 -> 案例迁移 -> DOE 采样 -> PBIPF 公式初筛 -> ABAQUS 校核 -> 案例回流 -> 设计报告输出。

当前主对话流程接入 `workflow/` 多智能体运行时。该运行时使用 LangGraph 状态图组织任务解析、候选生成、代理初筛、有限元校核、知识回流和报告导出，并通过 SQLite 记录运行事件、工具调用和状态快照。PyQt6 入口保留手动调试能力，同时通过运行时支持流程恢复、智能体审计和可视化状态追踪。

## 当前设计对象

- 壳体类型：外压圆柱耐压壳 `CYLINDRICAL`
- 几何变量：`length_mm`、`radius_mm`、`thickness_mm`
- 铺层变量：`alpha_deg`、`beta_deg`、`imperfection_ratio`
- 材料体系：`T700/Epoxy`、`T800G/5228`、`M40J/TDE-85`
- 工况：外部静水压力 `external_pressure_MPa`
- 目标：极限压力不低于 `ultimate_pressure_min_MPa`，并按面密度或质量目标排序
- 流程参数：候选池总数和初筛保留数由自然语言明确指定
- 候选来源初始比例：`LLM:案例迁移:DOE = 2:1:1`，实际来源统计以有效候选为准

普通长度、半径、厚度、铺层角或缺陷比写入 `geometry_reference`，用于设计中心和几何包络；明确固定的几何条件写入 `fixed_geometry`。普通几何参考值不会强制所有候选等于该数值。

## PBIPF 公式

快速筛选阶段使用 PBIPF 公式预测极限压力：

```text
P_PBIPF = d1 * lg(Q) * t / R
        + d2 * Q * D22 / (D33 - D12)
        + d3 * Q * Ir * L / A22
        + d0
```

其中 `Q` 为 ASME RD-1172 计算得到的线性屈曲压力。候选初筛阶段不调用 Abaqus；系统先用 `core/pressure_hull_profile.py` 计算 `asme_linear_buckling_pressure_MPa`，再作为 PBIPF 公式输入。公式系数位于 `config/param_ranges.yaml`，层合板刚度由 `core/pressure_hull_profile.py` 按经典层合板理论计算。

## 智能体

| 智能体 | 模块 | 当前职责 |
| --- | --- | --- |
| 任务解析 | `core/task_parser.py` | 规则解析外压、边界、几何参考值、固定几何约束、目标压力、候选池总数和初筛保留数 |
| 候选生成 | `agents/candidate_gen.py` | 按默认初始比例调度 LLM、案例迁移和 DOE；LLM 输入为系统整理后的工程任务书，输出为自然语言候选表；系统解析、校验并去重候选 |
| 快速筛选 | `agents/screener.py` | 使用 ASME RD-1172 线性屈曲压力和 PBIPF 公式预测极限压力并排序 |
| 有限元校核 | `agents/fem_agent.py` | 生成 ABAQUS 耐压壳脚本并读取标准结果 JSON |
| 知识回流 | `agents/knowledge_agent.py` | 写入案例库、案例记忆和代理公式校准数据 |
| 报告生成 | `agents/report_gen.py` | 基于结构化任务、初筛理由和有限元结果输出报告；工程解释与制造建议可由受控 LLM 补充 |

## 工作流运行时

| 模块 | 职责 |
| --- | --- |
| `workflow/runtime.py` | LangGraph 状态图运行时，支持启动、人工确认后继续、从快照恢复 |
| `workflow/agent_contracts.py` | 智能体职责契约，定义节点、工具、输入、输出、LLM 边界和失败策略 |
| `workflow/event_store.py` | SQLite 运行库，记录 `workflow_runs`、`workflow_events` 和 `workflow_snapshots` |
| `workflow/tool_registry.py` | 工具注册层，统一审计任务解析、候选生成、初筛、有限元、知识回流和报告工具调用 |
| `workflow/simulation_queue.py` | 有限元作业队列，记录候选入队、运行、成功、失败和结果摘要 |
| `workflow/state.py` | 工作流状态契约，保存任务、候选、初筛、正式有限元输入、有限元结果、知识回流结果、报告和人工确认状态 |

运行时数据写入 `data/runtime/`，该目录属于本地运行产物，不进入 Git。PyQt6 主界面包含“任务配置”页，展示结构化任务契约、用户已给事实、普通几何参考、固定几何约束、候选生成控制参数、初筛控制参数和事实边界；该页只读取当前会话任务，不修改候选或流程状态。“智能体流程”页可读取运行时事件库、状态快照和有限元作业队列，展示运行摘要、状态图、智能体职责契约、诊断信息、LLM 后端配置状态、LLM 调用轨迹、有限元作业队列和工具调用审计；该页提供“检测 LLM 后端”按钮，按主模型和回退模型逐个执行实时健康检查，检测结果只显示后端名称、模型、状态、耗时和脱敏错误摘要，不显示 URL、密钥或提示词正文。“候选方案”页展示候选来源构成、三路初始配额、规则过滤、结构去重和 DOE 补足审计；“结果追踪”页展示 TMP 会话候选、正式 C 编号、代理预测、FEM 结果、代理误差、CASE 回流状态和报告纳入状态之间的对应关系；“报告预览”页读取当前会话报告或 `data/results/latest_report.md`，展示 Markdown/PDF 路径、LLM 工程解释使用状态和 Markdown 正文预览。LLM 调用轨迹只记录后端名称、模型名称、调用状态、耗时和错误摘要，不记录 URL、密钥、系统提示词或用户提示词。重大阶段仍以源码、配置、测试和文档入库。

## 外部知识

运行时读取本项目 `knowledge/external` 中的外部知识库和知识图谱数据，路径配置在 `config/app_config.yaml`。该目录与 `CSDM_panel` 使用同一版外部知识资产结构：

- `knowledge/external/rag/rag_chunks.jsonl`：51788 条 RAG 文本块
- `knowledge/external/kg/`：2214 个实体、480899 条关系
- `knowledge/external/provenance/source_registry/`：1931 条源登记和 1931 条源元数据
- `knowledge/external/provenance/structured_text/documents.jsonl`：1931 条结构化文档
- `knowledge/external/provenance/structured_text/blocks.jsonl`：400762 条结构化文本块
- `knowledge/external/provenance/structured_text/table_records.jsonl`：22800 条表格记录
- `knowledge/external/provenance/structured_text/figure_records.jsonl`：44135 条图片记录
- `knowledge/external/provenance/structured_text/formula_records.jsonl`：108500 条公式记录
- `knowledge/external/provenance/structured_text/markdown_documents/`：1931 份 Markdown 全文

候选生成 LLM 使用 RAG 片段和知识图谱关系作为工程提案依据；RAG 检索结果按同一篇文献或同一来源去重，图谱证据在输出中合并为统一来源标签。结构化候选参数仍由系统解析、归一化、规则检查和 Schema 校验确定。

GUI 的“知识库”页展示案例库、外部知识资产状态、代理模型指标、RAG 命中文本块和知识图谱关系。该页面支持按当前任务自动检索，也支持人工输入工程检索词进行证据预览；证据用于审计候选生成 LLM 的工程上下文和人工核查来源，不作为确定性数值来源。

GUI 左侧“辅助入口”提供最近运行记录下拉框、刷新运行记录和载入运行快照按钮。载入快照只读取 `data/runtime/workflow_runtime.sqlite3` 中的最近状态，不重新调用 LLM、代理模型或 Abaqus；载入后会恢复任务、候选、筛选结果、有限元结果、报告和待确认节点。

## 启动

```powershell
D:\anaconda3\envs\GPT\python.exe main.py
```

环境自检：

```powershell
D:\anaconda3\envs\GPT\python.exe scripts\check_env.py
```

批量生成初始案例：

```powershell
D:\anaconda3\envs\GPT\python.exe scripts\build_initial_cases.py --reset --count 10 --task-count 1 --pressures 30 --target-pressure 35
```

`--reset` 会清理现有案例、任务、求解输入输出、Abaqus 工件、案例记忆索引和代理公式校准文件，再从 `CASE_1` 和 `C1` 重新计数。初始案例生成使用参数范围内的拉丁超立方采样；批量建库默认不写入会话任务编号，只有显式使用 `--record-task` 时才记录 `TASK_N` 追溯文件。

## 有限元说明

自动桥接脚本位于 `abaqus/runtime_build_pressure_hull.py`，使用 JSON 输入输出。流程先执行单位外压线性屈曲分析并提取一阶模态云图，再以一阶模态缺陷进入 Static Riks 后屈曲分析，极限压力取最大 LPF 与基准外压的乘积。

`reference/wangge.py` 与 `reference/zhangusdfld.for` 只作为人工建模和用户子程序参考，不属于主流程必需资产。`reference/zhangusdfld.for` 通过 `config/app_config.yaml` 的 `abaqus.use_user_subroutine` 显式启用，默认关闭以避免本机用户子程序编译环境阻断主流程。未找到 ABAQUS 命令时返回带诊断信息的失败结果，不伪造有限元通过。
