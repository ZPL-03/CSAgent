# CSDM_cph

复合材料耐压壳智能设计系统面向外压圆柱复合材料压力壳，主链路为：

自然语言需求 -> 用户事实抽取 -> LLM 自然语言候选提案 -> 案例迁移 -> DOE 采样 -> PBIPF 公式初筛 -> ABAQUS 校核 -> 案例记忆回流 -> 设计报告输出。

## 当前设计对象

- 壳体类型：外压圆柱耐压壳 `CYLINDRICAL`
- 几何变量：`length_mm`、`radius_mm`、`thickness_mm`
- 铺层变量：`alpha_deg`、`beta_deg`、`imperfection_ratio`
- 材料体系：`T700/Epoxy`、`T800G/5228`、`M40J/TDE-85`
- 工况：外部静水压力 `external_pressure_MPa`
- 目标：极限压力不低于 `ultimate_pressure_min_MPa`，并按面密度或质量目标排序
- 流程参数：候选池总数和初筛保留数由自然语言明确指定；候选来源初始配额按 `LLM:案例迁移:DOE = 2:1:1` 计算，实际来源统计以有效候选为准

## PBIPF 代理公式

快速筛选阶段使用 PBIPF 代理公式：

- `P_PBIPF = d1·lg(Q)·t/R + d2·Q·D22/(D33-D12) + d3·Q·Ir·L/A22 + d0`

其中 `Q` 为线性屈曲特征值。候选初筛阶段不会调用 Abaqus，而是由 `core/pressure_hull_profile.py` 按 ASME RD-1172 公式计算 `asme_linear_buckling_pressure_MPa`，再将该值作为 PBIPF 公式的 `Q` 输入。系数位于 `config/param_ranges.yaml`，层合板刚度由 `core/pressure_hull_profile.py` 按经典层合板理论计算；后续真实 Abaqus 结果会作为案例回流数据用于校准极限压力代理公式。

## 智能体

| 智能体 | 模块 | 当前职责 |
| --- | --- | --- |
| 任务解析 | `core/task_parser.py` | 规则解析外压、几何包络、材料、极限压力目标、候选池总数和初筛保留数 |
| 候选生成 | `agents/candidate_gen.py` | 按默认初始比例调度 LLM、案例迁移和 DOE；LLM 输入使用 SFT 风格的用户事实，输出为自然语言候选表，由系统解析为结构化候选；表格推荐理由覆盖结构性能依据和制造/缺陷风险依据；LLM 输出的候选行和回答片段进入候选追踪字段；LLM 和案例迁移候选缺少必要设计字段时不进入候选池 |
| 快速筛选 | `agents/screener.py` | 使用 ASME RD-1172 线性屈曲 Q 和 PBIPF 公式预测极限压力并排序 |
| 有限元校核 | `agents/fem_agent.py` | 生成 ABAQUS 耐压壳脚本并读取标准结果 JSON |
| 知识回流 | `agents/knowledge_agent.py` | 写入案例库、案例记忆和代理公式校准数据 |
| 报告生成 | `agents/report_gen.py` | 使用结构化数据确定性输出任务事实、初筛理由和有限元结果；工程解释与制造建议由受控 LLM 补充，调用失败时使用确定性解释 |

## 外部知识

运行时读取本项目 `knowledge/external` 中的外部知识库/知识图谱数据，路径配置在 `config/app_config.yaml`。该目录包含知识库文本块、知识图谱和溯源文档，主流程不依赖外部项目路径。候选生成 LLM 使用检索片段作为工程提案依据；结构化候选参数仍由系统解析、归一化、规则检查和 Schema 校验确定。

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

`--reset` 会清理旧案例、任务、求解输入输出、Abaqus 工件、案例记忆索引和代理公式校准文件，再从 `CASE_1` 和 `C1` 重新计数。初始案例生成使用参数范围内的拉丁超立方采样；批量建库默认不写入会话任务编号，只有显式使用 `--record-task` 时才记录 `TASK_N` 追溯文件。

## 有限元说明

`reference/wangge.py` 与 `reference/zhangusdfld.for` 保留为耐压壳参数化建模和用户子程序参考。当前自动桥接脚本位于 `abaqus/runtime_build_pressure_hull.py`，使用 JSON 输入输出，先执行单位外压线性屈曲分析并提取一阶模态云图，再以一阶模态缺陷进入 Static Riks 后屈曲分析，极限压力取最大 LPF 与基准外压的乘积。`reference/zhangusdfld.for` 通过 `config/app_config.yaml` 的 `abaqus.use_user_subroutine` 显式启用，默认关闭以避免本机用户子程序编译环境阻断主流程。未找到 ABAQUS 命令时返回带诊断信息的失败结果，不伪造有限元通过。
