## SIM / eSIM AI Agent 最终整体架构（Runtime Agent 架构版）

┌───────────────────────────────────────────────────────────────┐
│                         USER LAYER                           │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│ 用户输入：                                                     │
│                                                               │
│ - 查询规范                                                     │
│ - 读取卡数据                                                   │
│ - 创建 SCP80 / SCP03                                          │
│ - 下载 Profile                                                 │
│ - 安装 Applet                                                  │
│ - 卡片调试                                                     │
│ - APDU 分析                                                    │
│ - SW 分析                                                      │
│ - 动态协议探索                                                 │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                       │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Intent Analyzer                                              │
│                                                               │
│  不识别具体业务                                                │
│  而是识别：                                                    │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐     │
│  │ Execution Intent                                     │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ KNOWLEDGE_ONLY                                       │     │
│  │ REQUIRES_CARD                                        │     │
│  │ REQUIRES_APDU                                        │     │
│  │ REQUIRES_DYNAMIC_REASONING                           │     │
│  │ REQUIRES_MULTI_STEP_EXECUTION                        │     │
│  │ REQUIRES_CAPABILITY_DISCOVERY                        │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                               │
│                                                               │
│  Goal Planner                                                 │
│                                                               │
│  只生成高层目标：                                              │
│                                                               │
│  - read_imsi                                                  │
│  - establish_secure_channel                                  │
│  - download_profile                                           │
│  - discover_card_capabilities                                 │
│                                                               │
│  不生成完整 APDU 流程                                          │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                  DYNAMIC RUNTIME AGENT LOOP                  │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│                 ┌────────────────────┐                        │
│                 │    THINK NODE      │                        │
│                 │                    │                        │
│                 │ 当前状态分析        │                        │
│                 │ 下一步推理          │                        │
│                 │ 是否需要RAG         │                        │
│                 │ 是否需要Skill       │                        │
│                 └─────────┬──────────┘                        │
│                           │                                   │
│                           ▼                                   │
│                 ┌────────────────────┐                        │
│                 │  SKILL SELECTOR    │                        │
│                 │                    │                        │
│                 │ 选择下一步 Skill    │                        │
│                 └─────────┬──────────┘                        │
│                           │                                   │
│                           ▼                                   │
│                 ┌────────────────────┐                        │
│                 │   SKILL RUNTIME    │                        │
│                 │                    │                        │
│                 │ 执行 Skill          │                        │
│                 │ 更新 Runtime State  │                        │
│                 └─────────┬──────────┘                        │
│                           │                                   │
│                           ▼                                   │
│                 ┌────────────────────┐                        │
│                 │   OBSERVE NODE     │                        │
│                 │                    │                        │
│                 │ 分析 APDU 响应      │                        │
│                 │ 分析 SW             │                        │
│                 │ 分析卡能力          │                        │
│                 └─────────┬──────────┘                        │
│                           │                                   │
│                 finished? │                                   │
│                     ├──── yes ───► FINAL RESPONSE             │
│                     │                                         │
│                     └──── no ───► LOOP AGAIN                  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                     SKILL RUNTIME LAYER                      │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Skill Registry                                               │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐     │
│  │ Primitive Skills                                     │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ select_file                                          │     │
│  │ read_binary                                          │     │
│  │ read_record                                          │     │
│  │ verify_pin                                           │     │
│  │ authenticate                                          │     │
│  │ get_response                                          │     │
│  │ send_envelope                                         │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                               │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐     │
│  │ Composite Skills                                     │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ read_imsi                                            │     │
│  │ read_iccid                                           │     │
│  │ read_msisdn                                          │     │
│  │ read_spn                                             │     │
│  │ usim_authenticate                                    │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                               │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐     │
│  │ Exploratory Skills                                  │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ discover_card                                        │     │
│  │ detect_applications                                  │     │
│  │ detect_secure_channel                                │     │
│  │ scan_filesystem                                      │     │
│  │ probe_capabilities                                   │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                               │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐     │
│  │ Workflow Skills                                     │     │
│  ├──────────────────────────────────────────────────────┤     │
│  │ scp80_initialize                                     │     │
│  │ scp03_initialize                                     │     │
│  │ profile_download                                     │     │
│  │ gp_install_applet                                    │     │
│  │ ota_install                                          │     │
│  └──────────────────────────────────────────────────────┘     │
│                                                               │
│                                                               │
│  Skill Metadata                                               │
│                                                               │
│  - dangerous                                                  │
│  - requires_pin                                               │
│  - requires_secure_channel                                    │
│  - supported_card_types                                       │
│  - required_capabilities                                      │
│  - retry_policy                                                │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                     DSL / EXECUTION LAYER                    │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Skill DSL                                                    │
│                                                               │
│  workflow:                                                    │
│                                                               │
│    - skill: select_file                                       │
│      params:                                                  │
│        fid: 3F00                                              │
│                                                               │
│    - skill: select_file                                       │
│      params:                                                  │
│        fid: 7F20                                              │
│                                                               │
│    - skill: read_binary                                       │
│      params:                                                  │
│        offset: 0                                              │
│        length: 9                                              │
│                                                               │
│                                                               │
│  DSL Compiler                                                 │
│                                                               │
│  DSL                                                          │
│   ↓                                                           │
│  Skill                                                        │
│   ↓                                                           │
│  APDU Builder                                                 │
│   ↓                                                           │
│  APDU Queue                                                   │
│                                                               │
│                                                               │
│  APDU Builder                                                 │
│                                                               │
│  - build_select_file()                                        │
│  - build_read_binary()                                        │
│  - build_verify_pin()                                         │
│  - build_initialize_update()                                  │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                     TOOL RUNTIME LAYER                       │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  PCSC Runtime                                                 │
│                                                               │
│  - connect_reader                                             │
│  - reconnect_reader                                           │
│  - reset_card                                                 │
│  - send_apdu                                                  │
│  - disconnect                                                 │
│                                                               │
│                                                               │
│  Parser Runtime                                               │
│                                                               │
│  - parse_tlv                                                  │
│  - parse_fcp                                                  │
│  - parse_ber_tlv                                              │
│  - decode_sw                                                  │
│                                                               │
│                                                               │
│  Security Runtime                                             │
│                                                               │
│  - scp03                                                      │
│  - mac_verify                                                 │
│  - secure_messaging                                           │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                     RUNTIME STATE LAYER                      │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Runtime Context                                              │
│                                                               │
│  - connected                                                  │
│  - current_reader                                             │
│  - atr                                                        │
│  - selected_path                                              │
│  - current_application                                        │
│  - pin_verified                                               │
│  - secure_channel_state                                       │
│  - card_capabilities                                          │
│  - discovered_apps                                            │
│  - execution_history                                          │
│  - last_apdu                                                  │
│  - last_response                                              │
│                                                               │
│                                                               │
│  Checkpoint Manager                                           │
│                                                               │
│  - save_checkpoint                                            │
│  - restore_checkpoint                                         │
│  - replay_execution                                           │
│  - rollback_state                                             │
│                                                               │
│                                                               │
│  Retry Engine                                                 │
│                                                               │
│  - retryable_error_detection                                  │
│  - reconnect_and_resume                                       │
│  - restore_select_path                                        │
│  - retry_policy                                               │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                         RAG LAYER                            │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Hybrid Retrieval                                             │
│                                                               │
│  - BM25                                                       │
│  - Dense Vector                                               │
│  - Metadata Filter                                            │
│  - Reranker                                                   │
│                                                               │
│                                                               │
│  Structured Knowledge                                         │
│                                                               │
│  - ISO7816                                                    │
│  - ETSI TS 102 221                                            │
│  - 3GPP TS 31.102                                             │
│  - GlobalPlatform                                             │
│  - JavaCard                                                   │
│                                                               │
│                                                               │
│  Knowledge Graph                                              │
│                                                               │
│  - APDU Relations                                             │
│  - EF Relationships                                           │
│  - SW Mapping                                                 │
│  - Security Conditions                                        │
│  - File System Graph                                          │
│                                                               │
│                                                               │
│  Runtime RAG Usage                                            │
│                                                               │
│  Runtime 过程中：                                              │
│                                                               │
│  SW = 6982                                                    │
│      ↓                                                        │
│  动态查询规范                                                  │
│      ↓                                                        │
│  继续 Runtime 推理                                             │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                    PHYSICAL DEVICE LAYER                     │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  PCSC                                                         │
│   ├── Reader                                                  │
│   ├── SIM / USIM                                              │
│   ├── eUICC                                                   │
│   ├── JavaCard                                                │
│   └── Secure Element                                          │
│                                                               │
└───────────────────────────────────────────────────────────────┘

## 基于langchain+langgraph画出实现的流程图

┌──────────────────────────────────────────────────────────────┐
│                         USER INPUT                           │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                 LangGraph Entry Point                        │
│                                                              │
│ graph.invoke({                                               │
│    user_input: "...",                                        │
│    runtime_state: {},                                        │
│    observations: [],                                         │
│    current_goal: null                                        │
│ })                                                           │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                  Intent Analyzer Node                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ LangChain LLMChain                                           │
│                                                              │
│ 输入：                                                        │
│   用户问题                                                    │
│                                                              │
│ 输出：                                                        │
│   execution_intent                                           │
│                                                              │
│ 例如：                                                        │
│   KNOWLEDGE_ONLY                                             │
│   REQUIRES_CARD                                              │
│   REQUIRES_APDU                                              │
│   REQUIRES_DYNAMIC_REASONING                                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                     Goal Planner Node                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ LangChain Structured Output                                  │
│                                                              │
│ 输入：                                                        │
│   user_input                                                 │
│   execution_intent                                           │
│                                                              │
│ 输出：                                                        │
│                                                              │
│ {                                                            │
│   goal: "download_profile",                                  │
│   requires_runtime_loop: true                                │
│ }                                                            │
│                                                              │
│ 注意：                                                        │
│ 不生成完整APDU                                                │
│ 不生成完整流程                                                 │
│ 只生成高层目标                                                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
             ┌────────────────────────────────┐
             │ 是否需要 Runtime Agent Loop？ │
             └────────────────────────────────┘
                      │                │
                 NO   │                │ YES
                      │                ▼
                      │
                      │
                      │
                      ▼
┌──────────────────────────────────────────────────────────────┐
│                     Knowledge QA Node                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ LangChain RAG Chain                                          │
│                                                              │
│ retriever.invoke(query)                                      │
│                                                              │
│ → Vector Search                                              │
│ → BM25                                                       │
│ → Metadata Filter                                            │
│                                                              │
│ LLM 总结最终答案                                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                      │
                      ▼
                   END



################################################################
#################### Runtime Agent Loop #########################
################################################################


┌──────────────────────────────────────────────────────────────┐
│                  Runtime Think Node                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ LangChain Agent / LLM                                        │
│                                                              │
│ 输入：                                                        │
│   current_goal                                               │
│   runtime_state                                               │
│   observations                                                │
│                                                              │
│ 推理：                                                        │
│   下一步需要什么？                                             │
│                                                              │
│ 输出：                                                        │
│                                                              │
│ {                                                            │
│   next_action: {                                             │
│      skill: "discover_card"                                  │
│   }                                                          │
│ }                                                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                  Skill Selector Node                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ LangChain Tool Selection                                     │
│                                                              │
│ 根据：                                                        │
│   next_action                                                │
│                                                              │
│ 匹配 Skill Registry                                           │
│                                                              │
│ 输出：                                                        │
│   selected_skill                                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                  Skill Runtime Node                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 执行 Skill                                                    │
│                                                              │
│ 例如：                                                        │
│   discover_card                                              │
│   read_imsi                                                  │
│   scp03_initialize                                           │
│                                                              │
│ Skill 内部：                                                  │
│                                                              │
│   DSL                                                        │
│     ↓                                                        │
│   APDU Builder                                               │
│     ↓                                                        │
│   Tool Runtime                                               │
│     ↓                                                        │
│   PCSC                                                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                   Tool Runtime Node                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ connect_reader()                                             │
│ send_apdu()                                                  │
│ reset_card()                                                 │
│                                                              │
│ 真实卡片交互                                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                    Observe Node                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 分析执行结果                                                   │
│                                                              │
│ 输入：                                                        │
│   APDU Response                                               │
│   SW                                                          │
│   Runtime State                                               │
│                                                              │
│ 例如：                                                        │
│                                                              │
│   SW = 6982                                                  │
│                                                              │
│ → 是否需要 RAG？                                              │
│ → 是否需要 Retry？                                            │
│ → 是否需要恢复状态？                                           │
│ → 是否继续推理？                                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                             │
                ┌────────────┴─────────────┐
                │                          │
                ▼                          ▼
┌──────────────────────────┐   ┌──────────────────────────────┐
│      Retry Node          │   │      Runtime RAG Node        │
├──────────────────────────┤   ├──────────────────────────────┤
│                          │   │                              │
│ reconnect_reader()       │   │ 动态规范检索                  │
│ restore_state()          │   │                              │
│ replay_execution()       │   │ 例如：                        │
│                          │   │                              │
│ Retry Policy             │   │ “6982 meaning”               │
│                          │   │ “SCP80 initialize failed”    │
│                          │   │                              │
└────────────┬─────────────┘   └──────────────┬───────────────┘
             │                                │
             └────────────────┬───────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                  Runtime State Update Node                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 更新：                                                        │
│                                                              │
│ runtime_state = {                                            │
│   connected: true,                                           │
│   atr: "...",                                                │
│   selected_path: [...],                                      │
│   secure_channel: true,                                      │
│   capabilities: [...]                                        │
│ }                                                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
              ┌────────────────────────────┐
              │ 是否完成 current_goal？    │
              └────────────────────────────┘
                       │            │
                  NO   │            │ YES
                       │            ▼
                       │
                       │
                       ▼
          回到 Runtime Think Node



################################################################
######################## Final Response ########################
################################################################


┌──────────────────────────────────────────────────────────────┐
│                  Final Reasoning Node                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ LangChain LLM                                                │
│                                                              │
│ 汇总：                                                        │
│   - 用户目标                                                  │
│   - Runtime执行过程                                           │
│   - APDU结果                                                   │
│   - RAG内容                                                    │
│                                                              │
│ 输出最终解释：                                                 │
│                                                              │
│ “已成功建立 SCP03 通道”                                       │
│ “Profile 下载失败，原因是...”                                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                             │
                             ▼
                            END



##  一、整体目录结构
sim-agent/
│
├── app/
│
│   ├── main.py
│   ├── config/
│   │   ├── settings.py
│   │   └── logging.py
│   │
│   ├── graph/
│   │   ├── workflow.py
│   │   ├── runtime_loop.py
│   │   ├── routes.py
│   │   └── state.py
│   │
│   ├── nodes/
│   │   ├── intent/
│   │   │   └── intent_node.py
│   │   │
│   │   ├── planner/
│   │   │   └── goal_planner_node.py
│   │   │
│   │   ├── runtime/
│   │   │   ├── think_node.py
│   │   │   ├── observe_node.py
│   │   │   ├── retry_node.py
│   │   │   ├── rag_node.py
│   │   │   └── finalize_node.py
│   │   │
│   │   └── skill/
│   │       ├── skill_selector_node.py
│   │       └── skill_runtime_node.py
│   │
│   ├── models/
│   │   ├── llm.py
│   │   ├── embedding.py
│   │   └── structured_output.py
│   │
│   ├── runtime/
│   │   ├── context.py
│   │   ├── checkpoint.py
│   │   ├── retry_policy.py
│   │   ├── event_bus.py
│   │   └── state_manager.py
│   │
│   ├── skills/
│   │   ├── base/
│   │   │   ├── base_skill.py
│   │   │   ├── registry.py
│   │   │   └── metadata.py
│   │   │
│   │   ├── primitive/
│   │   │   ├── select_file.py
│   │   │   ├── read_binary.py
│   │   │   ├── read_record.py
│   │   │   ├── verify_pin.py
│   │   │   └── get_response.py
│   │   │
│   │   ├── composite/
│   │   │   ├── read_imsi.py
│   │   │   ├── read_iccid.py
│   │   │   ├── read_spn.py
│   │   │   └── usim_auth.py
│   │   │
│   │   ├── exploratory/
│   │   │   ├── discover_card.py
│   │   │   ├── probe_capabilities.py
│   │   │   ├── detect_secure_channel.py
│   │   │   └── scan_applications.py
│   │   │
│   │   └── workflow/
│   │       ├── scp03_initialize.py
│   │       ├── scp80_initialize.py
│   │       ├── profile_download.py
│   │       ├── ota_install.py
│   │       └── gp_install_applet.py
│   │
│   ├── dsl/
│   │   ├── compiler.py
│   │   ├── parser.py
│   │   ├── schema.py
│   │   └── validators.py
│   │
│   ├── apdu/
│   │   ├── builders/
│   │   │   ├── select_builder.py
│   │   │   ├── read_builder.py
│   │   │   ├── auth_builder.py
│   │   │   └── secure_channel_builder.py
│   │   │
│   │   ├── parsers/
│   │   │   ├── tlv_parser.py
│   │   │   ├── fcp_parser.py
│   │   │   ├── sw_parser.py
│   │   │   └── ber_tlv_parser.py
│   │   │
│   │   └── constants/
│   │       ├── sw_codes.py
│   │       ├── file_ids.py
│   │       └── instructions.py
│   │
│   ├── tools/
│   │   ├── pcsc/
│   │   │   ├── client.py
│   │   │   ├── connection.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── security/
│   │   │   ├── scp03.py
│   │   │   ├── mac.py
│   │   │   └── crypto.py
│   │   │
│   │   └── parser/
│   │       ├── tlv.py
│   │       └── ber.py
│   │
│   ├── rag/
│   │   ├── loader/
│   │   │   ├── pdf_loader.py
│   │   │   ├── spec_chunker.py
│   │   │   └── metadata_extractor.py
│   │   │
│   │   ├── vectorstore/
│   │   │   ├── chroma_store.py
│   │   │   └── faiss_store.py
│   │   │
│   │   ├── retriever/
│   │   │   ├── hybrid_retriever.py
│   │   │   ├── bm25.py
│   │   │   └── reranker.py
│   │   │
│   │   └── knowledge_graph/
│   │       ├── apdu_graph.py
│   │       ├── sw_graph.py
│   │       └── filesystem_graph.py
│   │
│   ├── prompts/
│   │   ├── intent/
│   │   ├── planner/
│   │   ├── runtime/
│   │   ├── reasoning/
│   │   └── rag/
│   │
│   └── utils/
│       ├── logger.py
│       ├── json_utils.py
│       └── async_utils.py
│
├── specs/
│   ├── iso7816/
│   ├── etsi/
│   ├── 3gpp/
│   ├── globalplatform/
│   └── javacard/
│
├── tests/
│   ├── skills/
│   ├── apdu/
│   ├── runtime/
│   └── graph/
│
├── data/
│   ├── vector_db/
│   ├── checkpoints/
│   └── logs/
│
├── requirements.txt
├── docker-compose.yml
└── README.md

## 二、核心 Runtime State
app/graph/state.py
```python
from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):

    # 用户输入
    user_input: str

    # execution intent
    execution_intent: str

    # 当前目标
    current_goal: str

    # runtime loop
    observations: List[Dict[str, Any]]

    # 当前skill
    current_skill: str

    # runtime context
    runtime_state: Dict[str, Any]

    # rag results
    rag_context: List[str]

    # retry
    retry_count: int

    # final
    final_response: str

    # finish
    finished: bool
```

## 三、LLM 初始化
app/models/llm.py

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0,
    base_url="http://localhost:8000/v1",
    api_key="test"
)
```

## 四、Intent Node
app/nodes/intent/intent_node.py

```python
from app.models.llm import llm
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template("""
分析用户请求。

只识别 execution intent。

可选：

- KNOWLEDGE_ONLY
- REQUIRES_CARD
- REQUIRES_APDU
- REQUIRES_DYNAMIC_REASONING

用户输入:
{input}
""")

def intent_node(state):

    chain = prompt | llm

    result = chain.invoke({
        "input": state["user_input"]
    })

    return {
        "execution_intent": result.content.strip()
    }
```

## 五、Goal Planner Node
app/nodes/planner/goal_planner_node.py

```python
from app.models.llm import llm
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template("""
用户目标分析。

不要生成APDU。

只生成高层 goal。

用户:
{input}
""")

def goal_planner_node(state):

    chain = prompt | llm

    result = chain.invoke({
        "input": state["user_input"]
    })

    return {
        "current_goal": result.content.strip()
    }
```

## 六、Runtime Think Node（核心）
app/nodes/runtime/think_node.py

```python
from app.models.llm import llm

def think_node(state):

    prompt = f"""
当前目标:

{state['current_goal']}

当前runtime state:

{state['runtime_state']}

历史 observations:

{state['observations']}

请决定下一步 skill。
"""

    result = llm.invoke(prompt)

    return {
        "next_action": result.content
    }
```

## 七、Skill 基类
app/skills/base/base_skill.py

```python
class BaseSkill:

    name = "base"

    description = ""

    dangerous = False

    requires_pin = False

    async def run(self, ctx, params):

        raise NotImplementedError
```

## 八、Skill Registry
app/skills/base/registry.py

```python
SKILLS = {}

def register(skill):

    SKILLS[skill.name] = skill

def get_skill(name):

    return SKILLS[name]
```    

## 九、Primitive Skill 示例
app/skills/primitive/select_file.py

```python
from app.skills.base.base_skill import BaseSkill
from app.apdu.builders.select_builder import build_select_file

class SelectFileSkill(BaseSkill):

    name = "select_file"

    async def run(self, ctx, params):

        fid = params["fid"]

        apdu = build_select_file(fid)

        result = await ctx.pcsc.send_apdu(apdu)

        ctx.selected_path.append(fid)

        return result
```        

## 十、Composite Skill 示例
app/skills/composite/read_imsi.py

```python
class ReadImsiSkill(BaseSkill):

    name = "read_imsi"

    async def run(self, ctx, params):

        await ctx.execute_skill(
            "select_file",
            {"fid": "3F00"}
        )

        await ctx.execute_skill(
            "select_file",
            {"fid": "7F20"}
        )

        await ctx.execute_skill(
            "select_file",
            {"fid": "6F07"}
        )

        return await ctx.execute_skill(
            "read_binary",
            {
                "offset": 0,
                "length": 9
            }
        )
```

## 十一、PCSC Runtime
app/tools/pcsc/client.py
建议使用：

pyscard GitHub https://github.com/LudovicRousseau/pyscard?utm_source=chatgpt.com

```python
from smartcard.System import readers

class PcscClient:

    def __init__(self):

        self.connection = None

    def connect(self):

        r = readers()

        reader = r[0]

        self.connection = reader.createConnection()

        self.connection.connect()

    async def send_apdu(self, apdu):

        data, sw1, sw2 = self.connection.transmit(apdu)

        return {
            "data": data,
            "sw": f"{sw1:02X}{sw2:02X}"
        }
```

## 十二、APDU Builder
app/apdu/builders/select_builder.py

```python
def build_select_file(fid: str):

    return bytes.fromhex(
        f"00A4000002{fid}"
    )
```    

## 十三、Observe Node
app/nodes/runtime/observe_node.py

```python
def observe_node(state):

    last = state["observations"][-1]

    sw = last.get("sw")

    if sw != "9000":

        return {
            "need_retry": True
        }

    return {
        "need_retry": False
    }
```

## 十四、Retry Node
app/nodes/runtime/retry_node.py

```python
def retry_node(state):

    retry_count = state["retry_count"]

    if retry_count > 3:

        return {
            "finished": True,
            "final_response": "Retry failed"
        }

    return {
        "retry_count": retry_count + 1
    }
```

## 十五、RAG Retriever
app/rag/retriever/hybrid_retriever.py

```python
class HybridRetriever:

    def retrieve(self, query):

        # BM25
        # Vector
        # Rerank

        return docs
```

## 十六、LangGraph Workflow（最核心）
app/graph/workflow.py

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)

workflow.add_node("intent", intent_node)

workflow.add_node("planner", goal_planner_node)

workflow.add_node("think", think_node)

workflow.add_node("skill", skill_runtime_node)

workflow.add_node("observe", observe_node)

workflow.add_node("retry", retry_node)

workflow.add_node("finalize", finalize_node)

workflow.set_entry_point("intent")

workflow.add_edge("intent", "planner")

def route_after_planner(state):

    if (
        state["execution_intent"]
        == "KNOWLEDGE_ONLY"
    ):
        return "finalize"

    return "think"

workflow.add_conditional_edges(
    "planner",
    route_after_planner
)

workflow.add_edge("think", "skill")

workflow.add_edge("skill", "observe")

def route_after_observe(state):

    if state.get("need_retry"):
        return "retry"

    if state["finished"]:
        return "finalize"

    return "think"

workflow.add_conditional_edges(
    "observe",
    route_after_observe
)

workflow.add_edge("retry", "skill")

workflow.add_edge("finalize", END)

graph = workflow.compile()
```

## 十七、主程序
app/main.py

```python
from app.graph.workflow import graph

def main():

    while True:

        user_input = input("> ")

        result = graph.invoke({

            "user_input": user_input,

            "runtime_state": {},

            "observations": [],

            "finished": False,

            "retry_count": 0
        })

        print(result["final_response"])

if __name__ == "__main__":
    main()
```

## 十八、推荐开发阶段（非常重要）
Phase 1

先做：

PCSC
APDU Builder
Primitive Skills
Runtime State
Phase 2

再做：

LangGraph Runtime Loop
Retry
Recovery
Observe Node
Phase 3

最后做：

Dynamic Runtime Reasoning
Runtime RAG
Capability Discovery
SCP03
eSIM
十九、真正核心（务必记住）

你的系统：

不是：
ChatBot + Tool Call
而是：
Runtime Agent OS

LLM 只是：

策略控制器

真正核心：

Runtime State
Skill Runtime
APDU Runtime
Retry Engine
Capability Discovery
Recovery System
Protocol Constraints

这是整个系统最重要的部分。    





## 最终实现的节点流程图 

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LangGraph Runtime Agent Workflow                 │
└─────────────────────────────────────────────────────────────────────┘

                              ┌──────────┐
                              │  START   │
                              └──────────┘
                                   │
                                   ▼
                         ┌─────────────────┐
                         │   intent_node   │
                         │   (意图识别)     │
                         └─────────────────┘
                                   │
                                   ▼
                         ┌─────────────────┐
                         │ goal_planner    │
                         │   (目标规划)     │
                         └─────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │   route_after_planner       │
                    ▼                             ▼
            ┌──────────────┐              ┌─────────────────┐
            │ KNOWLEDGE_ONLY│              │   think_node    │
            │               │              │   (思考推理)     │
            └               │              └─────────────────┘
            │               │                       │
            │               │                       ▼
            │               │              ┌─────────────────┐
            │               │              │ skill_selector  │
            │               │              │   (技能选择)     │
            │               │              └─────────────────┘
            │               │                       │
            │               │                       ▼
            │               │              ┌─────────────────┐
            │               │              │ skill_runtime   │
            │               │              │   (技能执行)     │
            │               │              └─────────────────┘
            │               │                       │
            │               │                       ▼
            │               │              ┌─────────────────┐
            │               │              │  observe_node   │
            │               │              │   (观察结果)     │
            │               │              └─────────────────┘
            │               │                       │
            │               │    ┌──────────────────┴──────────────────┐
            │               │    │       route_after_observe           │
            │               │    │         (四路路由)                   │
            │               │    ▼                                     ▼
            │               │  ┌──────────┐                    ┌──────────────┐
            │               │  │ finished │                    │   continue   │
            │               │  │  =true   │                    │              │
            │               │  └     │    │                    │              │
            ▼               │  │     │    │                    ▼              │
   ┌─────────────────┐     │  │     │    │            ┌─────────────────┐    │
   │  finalize_node  │◄────┼──┼─────┼────┼────────────┤   think_node    │◄───┤
   │   (最终响应)     │     │  │     │    │            │   (继续思考)     │    │
   └─────────────────┘     │  │     │    │            └─────────────────┘    │
            │              │  │     │    │                    │              │
            ▼              │  │     │    └────────────────────┼──────────────┤
   ┌──────────┐            │  │     │                         │              │
   │   END    │            │  │     │                         ▼              │
   └──────────┘            │  │     │                ┌─────────────────┐    │
                           │  │     │                │   retry_node    │    │
                           │  │     │                │   (重试处理)     │    │
                           │  │     │                └─────────────────┘    │
                           │  │     │                         │              │
                           │  │     │                         └──────────────┤
                           │  │     │                                        │
                           │  │     │                         ┌──────────────┘
                           │  │     │                         │
                           │  │     ▼                         ▼
                           │  │  ┌─────────────────┐  ┌─────────────────┐
                           │  │  │ runtime_rag     │  │   think_node    │
                           │  │  │   (RAG查询)      │─►│   (继续思考)    │
                           │  │  └─────────────────┘  └─────────────────┘
                           │  │                           │
                           │  └───────────────────────────┘
                           │
                           └──► (SW失败触发RAG查询)
```

### 简化流程图

```
START → intent → planner ─┬─→ think → skill_selector → skill_runtime → observe
                          │                                           │
                          │                      ┌────────────────────┴────────────────┐
                          │                      │         route_after_observe        │
                          │                      │             (四路路由)              │
                          │                      ▼                                     ▼
                          │               ┌──────────────┐                    ┌────────────┐
                          │               │ need_retry   │                    │  finished  │
                          │               │    retry     │                    │  finalize  │
                          │               └───┬──────────┘                    └─────┬──────┘
                          │                   │                                     │
                          │                   ▼                                     ▼
                          │               ┌──────────────┐                         END
                          │               │ need_rag     │
                          │               │ runtime_rag  │
                          │               └───┬──────────┘
                          │                   │
                          └───────────────────┴───► think (循环)
```

### 四路路由逻辑

**定义**: observe_node 执行完成后，根据观察结果状态，有四种可能的路径选择：

```
                        observe_node (观察执行结果)
                              │
                              ▼
                    ┌─────────────────────┐
                    │   route_after_observe│
                    │     (四路路由判断)    │
                    └─────────────────────┘
                              │
         ┌────────────┬───────┴───────┬────────────┐
         │            │               │            │
         ▼            ▼               ▼            ▼
    ┌─────────┐ ┌───────────┐  ┌──────────┐ ┌──────────┐
    │ 路径1   │ │ 路径2     │  │ 路径3    │ │ 路径4    │
    │finalize │ │runtime_rag│  │  retry   │ │  think   │
    └─────────┘ └───────────┘  └──────────┘ └──────────┘
         │            │               │            │
         ▼            ▼               ▼            ▼
       END      → think          → think      → skill_selector
                 (带RAG上下文)    (调整参数)     (继续执行)
```

**各路径触发条件**:

| 路径 | 目标节点 | 触发条件 | 场景示例 |
|------|----------|----------|----------|
| 路径1 | `finalize` | `finished=true` | 任务全部完成，如成功读取IMSI |
| 路径2 | `runtime_rag` | `need_rag=true` | SW=6982（PIN未验证），需查知识库解释 |
| 路径3 | `retry` | `need_retry=true` | SW=6F00（通信异常），可重试 |
| 路径4 | `think` | 默认（以上都不满足） | 还有更多技能要执行，继续循环 |

### 主执行循环

```
┌────────────────────────────────────────────────────────────┐
│                    主执行循环                               │
│                                                            │
│   think → skill_selector → skill_runtime → observe        │
│                              │                             │
│                              ▼                             │
│                    ┌─────────────────┐                     │
│                    │ route_after_    │                     │
│                    │    observe      │                     │
│                    └─────────────────┘                     │
│                      │         │                           │
│                      ▼         ▼                           │
│                   retry    runtime_rag                     │
│                      │         │                           │
│                      └─────────┼──► think (循环)           │
│                                │                           │
│                                ▼                           │
│                           finalize → END                   │
└────────────────────────────────────────────────────────────┘
```

### runtime_rag_node 创新点

执行失败时的智能处理流程：

```
skill_runtime → observe (检测 SW != 9000)
                    │
                    ▼
            ┌──────────────────┐
            │ runtime_rag_node │
            │                  │
            │ 查询知识库:       │
            │ - SW 6982: PIN未验证
            │ - SW 6A82: 文件未找到
            │ - SW 6983: PIN已锁定
            │                  │
            │ 返回错误解释和建议 │
            └──────────────────┘
                    │
                    ▼
               think_node
            (根据RAG建议调整策略)
```

### 节点说明表

| 节点 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `intent_node` | 解析用户意图 | `user_input` | `execution_intent` |
| `goal_planner_node` | 制定执行计划 | `execution_intent` | `plan`, `goal` |
| `think_node` | 推理下一步动作 | `state`, `history` | `thought`, `next_skill` |
| `skill_selector_node` | 选择要执行的技能 | `next_skill` | `selected_skill`, `params` |
| `skill_runtime_node` | 执行技能并获取结果 | `selected_skill` | `skill_result`, `sw` |
| `observe_node` | 分析执行结果 | `skill_result` | `finished`, `need_retry`, `need_rag` |
| `retry_node` | 处理重试逻辑 | `retry_count` | `retry_params` |
| `runtime_rag_node` | 查询知识库解释SW错误 | `sw`, `skill_result` | `rag_context` |
| `finalize_node` | 生成最终响应 | `state` | `response`, `summary` |