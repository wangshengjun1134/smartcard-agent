## ADDED Requirements

### Requirement: LangGraph 工作流初始化

系统 SHALL 创建 LangGraph StateGraph 工作流，包含 Intent、Planner、Think、Skill、Observe、Finalize Nodes。

#### Scenario: 验证工作流结构
- **WHEN** 检查 `agents/graph/workflow.py`
- **THEN** 存在 StateGraph 定义，包含所有核心 Nodes 和 conditional edges

### Requirement: Intent Analyzer Node

系统 SHALL 实现 Intent Analyzer Node，识别用户请求的 execution_intent（KNOWLEDGE_ONLY, REQUIRES_CARD, REQUIRES_APDU, REQUIRES_DYNAMIC_REASONING）。

#### Scenario: 识别知识库查询意图
- **WHEN** 用户输入 "什么是 IMSI"
- **THEN** Intent Analyzer 返回 execution_intent = "KNOWLEDGE_ONLY"

#### Scenario: 识别读卡意图
- **WHEN** 用户输入 "读取卡上的 IMSI"
- **THEN** Intent Analyzer 返回 execution_intent = "REQUIRES_CARD"

### Requirement: Goal Planner Node

系统 SHALL 实现 Goal Planner Node，生成高层目标（如 read_imsi, establish_secure_channel），不生成完整 APDU 流程。

#### Scenario: 生成读卡目标
- **WHEN** execution_intent = "REQUIRES_CARD" 且用户请求读取 IMSI
- **THEN** Goal Planner 返回 current_goal = "read_imsi"

### Requirement: Runtime Think Node

系统 SHALL 实现 Runtime Think Node，基于当前目标、runtime_state 和 observations 推理下一步 Skill。

#### Scenario: 推理下一步 Skill
- **WHEN** current_goal = "read_imsi" 且 runtime_state.connected = True
- **THEN** Think Node 输出 next_action 包含 skill 名称和参数

### Requirement: Runtime Observe Node

系统 SHALL 实现 Observe Node，分析 APDU 响应和 SW，判断是否需要 Retry 或 RAG 查询。

#### Scenario: 分析成功响应
- **WHEN** APDU 响应 SW = "9000"
- **THEN** Observe Node 返回 need_retry = False

#### Scenario: 分析失败响应
- **WHEN** APDU 响应 SW = "6982"
- **THEN** Observe Node 返回 need_rag = True，查询 SW 含义

### Requirement: Agent State 结构

系统 SHALL 定义 AgentState TypedDict，包含 user_input, execution_intent, current_goal, observations, runtime_state, rag_context, retry_count, final_response, finished 字段。

#### Scenario: 验证 State 定义
- **WHEN** 检查 `agents/graph/state.py`
- **THEN** AgentState TypedDict 包含所有必需字段