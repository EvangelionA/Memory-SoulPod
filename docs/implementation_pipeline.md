# SoulPod 后续 Pipeline 详细实现指南

本文档依据 **`Core/core.md`**、**`Core/description.md`** 的产品与架构约束，并参考 **`clonellm-0.4.0`**（LiteLLM + LangChain 编排思路），给出 **从当前可运行基线到完整三位一体闭环** 的分阶段实现路线。

**范围说明：**

- 本文档仅描述设计与实施步骤，**不替代** `Core/*.md` 中的规范性原文；若冲突，以 `Core/` 为准并同步修订本文档。
- 实施时须遵守 **「不破坏现有前端与 API 行为」** 的兼容策略（见第 2 节），新能力通过 **配置开关、可选字段、默认路径** 引入。

---

## 0. 文档目的与读者

| 读者 | 用途 |
|------|------|
| 核心开发者 | 按阶段落地代码与目录，控制依赖与风险 |
| 产品与伦理审查 | 对照「金规则」检查每阶段是否可被用户误解或滥用 |
| 后续接手者 | 理解为何采用某编排方式（CloneLLM 对照）与 SoulPod 差异 |

---

## 1. 原则与约束（与 Core 对齐）

### 1.1 三位一体（The Trinity）

所有运行时逻辑应能明确归类到以下之一（见 `Core/core.md` 第 2 节、`description.md` 第 3 节）：

1. **长期记忆 (RAG Memory)**：`memories/` 中的可检索事实与情感片段，**非**模型权重。
2. **人物画像 (User Profile)**：`profile.json` 结构化字段（含 Big Five 0–1、关系、语言风格等）。
3. **行为规范 (System Prompts)**：`system_prompts.txt` + 代码内 **金规则（Golden Rules）** 常量。

**实现纪律：** 不要把「人设长文」只写死在代码里而不版本化；不要把「可检索记忆」只塞进 system prompt 而不走 RAG（否则难更新、难审计）。

### 1.2 金规则（Golden Rules）

摘自 `Core/core.md` 第 4 节，**必须在 prompt 与检索失败分支中可执行**：

- **拒绝幻觉**：记忆库无依据时，允许「模糊印象」，**禁止编造关键人生经历**（具体事件、日期、承诺等）。
- **去 AI 化**：禁止模型自称为「AI / 模型 / 指令 / 算法」；用户侧文案亦应避免破坏沉浸（前端错误提示可技术性，但回复内容需产品化）。
- **隐私至上**：默认本地/用户可控存储；日志与可观测性**不得**打印完整 `profile`、记忆正文、API Key。

### 1.3 DigitalTwinPackage（资产包）

标准目录见 `description.md` 第 4 节。代码侧已有占位：

- 加载器：`src/soulpod/package_loader.py`（`load_soul_package`）
- Schema 占位：`src/soulpod/schemas/profile.py`、`package_config.py`
- Prompt 组装占位：`src/soulpod/prompts/builder.py`、`golden_rules.py`
- RAG / 会话占位：`src/soulpod/memory/*`、`src/soulpod/chat/*`

**注意：** 真实亲人数据 **不要** 提交到公共仓库；`packages/` 仅示例与模板。

### 1.4 与「当前功能不破坏」的硬约束

以下为用户已依赖的契约（见 `docs/routes.md`）：

| 契约项 | 要求 |
|--------|------|
| 启动 | `python -m src.core` 仍启动 `src.server:app` |
| 页面 | `GET /`、`GET /settings` 仍返回现有 HTML |
| 对话 | `POST /chat`、`POST /chat/stream` 请求体仍为 `{ "messages": [...] }`，**默认行为**与接入包前一致 |
| 配置 | `GET/POST /api/runtime-config` 字段语义保持向后兼容；新增字段仅追加 |
| 前端 | `index.html` 默认仍可 `fetch` 固定 API；若新增「载体路径」等，须 **可选** 且默认不发送 |

**推荐兼容策略：**

1. **默认**：`system_prompt` 仍仅来自 `config/app_runtime.json`（与现网一致）。
2. **可选**：当 `app_runtime.json`（或后续字段）指定 `soul_package_path` 且目录合法时，将 `build_system_prompt(package, runtime_system_prompt)` 的结果注入为 **唯一一条** `role: system` 消息（或合并策略写清，见第 6 节）。
3. **关断**：路径为空或加载失败时，**回退**到当前逻辑，并在服务端打 **warning 级**日志（不含隐私内容）。

---

## 2. 当前基线（Baseline）

### 2.1 运行时数据流（现状）

1. 浏览器 `index.html` 维护 `chatHistory`，`POST /chat/stream` 发送完整历史。
2. `src/server.py` 读取 `config/app_runtime.json`，将其中 `system_prompt` **前置**为一条 system 消息（`_messages_with_system`）。
3. `src/liteLLM.py` 通过 `litellm.acompletion` 调用模型，SSE 返回 delta。

### 2.2 现状与目标差距

| 能力 | 现状 | 目标（三位一体） |
|------|------|------------------|
| 人物画像 | 无结构化 profile，仅靠自由文本 system | `profile.json` 校验 + 注入 |
| 长期记忆 | 无 RAG | `memories/` 向量检索 + 无命中策略 |
| 行为规范 | 用户手写 system + 无统一金规则落地 | 金规则常量 + `system_prompts.txt` 分层 |
| 会话记忆 | 前端全量上传 | 可保留或引入服务端 session（二选一为主） |

---

## 3. 与 CloneLLM（clonellm-0.4.0）的对照

CloneLLM 是 **「LiteLLM + LangChain 编排 + 可选 RAG + 可选会话记忆」** 的参考实现，SoulPod **借鉴编排分层**，**不照搬**「人类克隆」话术与产品目标。

### 3.1 可借鉴的实现要点

| CloneLLM 组件（路径示意） | 作用 | SoulPod 迁移建议 |
|---------------------------|------|------------------|
| `ChatLiteLLM` + `get_llm_provider` / api_key 注入（`_base.py`） | 统一多厂商模型 | 已有 `litellm`；若用 LangChain，再包一层 `ChatLiteLLM`，**api_base** 与 **api_key** 与现配置对齐 |
| `get_context_prompt` + `additional_system_prompts`（`_prompt.py`） | 多层 system 模板 | 对应：`golden_rules` + `system_prompts.txt` + `profile` 摘要 + `runtime` 补丁 |
| `user_profile_prompt` + `UserProfile`（`models.py`） | 结构化人设注入 JSON | 扩展 `SoulProfile` 字段与 `description.md` 表格一致；注入时控制 token |
| `summarize_context_prompt` + `fit()`（`core.py`） | 无 embedding 时摘要文档为静态 context | SoulPod 可选「冷启动」：无向量库时仅用摘要块（**注意幻觉风险**，需人工审核摘要） |
| Embedding + VectorStore + retriever（`core.py`） | RAG | 在 `RAGStoreStub` 落地；向量库文件放 `memories/` |
| `RunnableWithMessageHistory` + `MessagesPlaceholder`（`core.py`） | 服务端多轮 | **谨慎**：前端已传全量 history 时不要双重记忆（见第 9 节） |
| `InMemoryHistory` + `session_id`（`memory.py`） | 会话分桶 | 若采用服务端记忆，需后续换 **持久化**（SQLite/Redis/文件），否则重启丢上下文 |

### 3.2 不应照搬的部分

- **System 文案**：Clone 强调「你就是我、第一人称克隆」；SoulPod 是 **特定亲属 + 关系 + 情感边界**（`description.md` 3.3）。
- **伦理与幻觉**：SoulPod 场景对 **事实性** 更敏感，需在 prompt 中明确 **无检索命中** 时的说话方式，并考虑 **拒答模板**（非医疗/法律建议等，`core.md` 行为规范）。
- **记忆存储**：Clone 示例多为进程内；SoulPod 应优先 **用户本地包** 与 **可导出资产**。

---

## 4. 目标架构总览（逻辑 Pipeline）

下列为 **一次用户消息** 的理想处理管线（实施可分阶段启用）：

```text
[HTTP Request]
    -> 解析 messages +（可选）session_id +（可选）soul_package_path
    -> [Package Load] profile.json, config.json, system_prompts.txt
    -> [Prompt Build]
          golden_rules (code)
        + system_prompts.txt (asset)
        + profile compact injection (JSON or bullet summary)
        + runtime system_prompt from app_runtime.json (user override, optional)
    -> [RAG Retrieve] query = latest user turn (or full context policy)
          -> top_k chunks from memories/ (with scores)
        -> if empty / low score: attach "no_evidence" hint block to prompt (not shown to user)
    -> [History Assembly]
          Option A: trust client messages[] as full history (current)
          Option B: server-side window + RunnableWithMessageHistory
    -> [LLM Call] stream or non-stream
    -> [HTTP Response] SSE or JSON
```

**日志与可观测性：** 仅记录 session_id、包 id、检索条数、耗时；**禁止**记录用户消息全文与检索片段全文（除非用户明确开启本地调试模式并本地化存储）。

---

## 5. 阶段 0：工程打底（巩固现状）

**目标：** 保证基线可复现，文档与目录一致。

**步骤：**

1. 确认 `requirements.txt` 与运行环境（Python 版本）在 README 中一致。
2. 确认 `config/app_runtime.example.json` 不含真实密钥；真实配置在 `.gitignore` 中（若尚未忽略 `app_runtime.json`，应在实施密钥管理时处理）。
3. 在团队中固定术语：**Package**、**Profile**、**RAG**、**Runtime config**。

**验收：** 新成员可按 README 启动并完成一次流式对话。

**注意事项：** 本阶段不改用户可见行为。

---

## 6. 阶段 A：载体加载与 System Prompt 组装（接入 HTTP，开关式）

**目标：** 在 **不改变默认行为** 的前提下，允许从 DigitalTwinPackage 加载人设与规范文本。

### 6.1 配置设计（建议）

在 `app_runtime.json` **追加** 可选字段（示例名，实施时以代码为准）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `soul_package_path` | string | 绝对路径或相对项目根的路径；空表示关闭 |
| `soul_package_enabled` | bool | 显式开关，默认 `false`，避免误读路径 |

**兼容规则：**

- `soul_package_enabled == false` 或路径为空：**完全等同**当前逻辑（仅用 `system_prompt`）。
- 启用且加载成功：`build_system_prompt(package, runtime_system_prompt)`。
- 加载失败：**回退**当前逻辑，并记录 warning（不含路径以外的隐私）。

### 6.2 Schema 演进（profile.json / config.json）

1. 按 `description.md` 3.1 扩展 `SoulProfile`：Basic Info、Personality、Linguistic、Interests。
2. `PackageConfig` 增加：`embedding_model`、`retrieval_top_k`、`similarity_threshold`、`chunk_size` 等。
3. **版本字段**：在 JSON 根增加 `"schema_version": 1`，便于迁移。

**注意事项：**

- Pydantic 校验失败时的用户提示应 **generic**（「载体包格式错误」），详细信息写本地日志。
- `profile` 注入过长会挤占上下文：建议 **摘要层**（代码生成 0.5k–1k 字的「画像摘要」）+ 完整 JSON 仅离线工具使用。

### 6.3 与前端关系

- **最小改动路径：** 仅后端读取 `app_runtime.json`；用户在设置页手动编辑路径（后续再做 UI 字段）。
- **若增加 UI：** 在 `settings.html` 增加可选输入框，**默认留空**；保存到 `POST /api/runtime-config` 新字段。

**验收：**

- 关闭开关时，与阶段 0 行为逐字一致（同一 `messages` 输入输出风格一致）。
- 开启且包合法时，回复体现 `system_prompts.txt` 与 profile 摘要中的设定。

---

## 7. 阶段 B：对话编排层（统一入口）

**目标：** 将 `server.py` 内「拼消息 + 调 LLM」收敛到 `src/soulpod/chat/service.py`（或同级模块），`server` 仅薄路由。

### 7.1 两条技术路线（二选一或并存）

| 路线 | 优点 | 缺点 | 适用 |
|------|------|------|------|
| **B1. 继续 LiteLLM 直连**（现状） | 依赖少，流式简单 | 自管消息模板与 RAG 拼接 | 快速上线 RAG |
| **B2. LangChain LCEL**（CloneLLM 风格） | Runnable、历史、工具扩展统一 | 依赖多，SSE 需对齐 `astream` | 需要 Agent / 工具链时 |

**建议：** 先 **B1 完成 RAG**，再按需引入 **B2** 的子集（例如仅 `ChatPromptTemplate` + `StrOutputParser`，未必全量 Agent）。

### 7.2 流式（SSE）注意事项

当前 `server.py` 使用自定义 SSE 格式（`data: {"delta":...}`）。若改用 LangChain：

1. 确认 `astream` 的 chunk 形态与空增量过滤。
2. 保持 **前端协议不变**，或同时做前后端版本协商（不推荐在未必要时改前端）。

**验收：** 接口契约不变；延迟与错误码与现网可比（502 等）。

---

## 8. 阶段 C：RAG 长期记忆（memories/）

**目标：** 实现 `memories/` 下向量索引的 **构建（index）** 与 **查询（retrieve）**，并把结果注入 prompt。

### 8.1 索引构建（离线或管理接口）

1. 输入：`raw_memories.json` 或工具链输出的分块 JSON（阶段 E）。
2. 分块：参考 CloneLLM `CharacterTextSplitter` 思路，chunk_size / overlap 写入 `config.json`。
3. Embedding：与 LiteLLM 支持的 embedding 对齐，**密钥与 base** 与 chat 分离配置或共用（写清）。
4. 持久化：优先 **Chroma persist** 或 **FAISS + 元数据文件** 落在 `memories/`，与 `description.md` 中 `index.bin / .sqlite` 描述兼容即可（实现任选，但须在包内 README 说明）。

### 8.2 检索与注入

1. 查询文本：默认取 **最后一轮 user** 内容；高级：多 query 或 HyDE（后期）。
2. `top_k` 与 **分数阈值**：低于阈值则视为 **无有效记忆**（减少胡编）。
3. Prompt 结构建议：

```text
[Golden rules]
[System prompts from package]
[Profile summary]
[Retrieved memories - labeled as "可能相关的记忆摘录，非完整生平"]
[User messages...]
```

4. **无命中分支：** 明确指示模型使用「模糊印象」话术，**不**捏造细节（与 `Core` 一致）。

**验收：**

- 有关键记忆时，回答能引用摘录中的事实（仍建议避免逐字背诵隐私给用户以外的人）。
- 无记忆时，不出现具体虚构日期/事件。

**注意事项：** RAG 不是隐私屏障；包文件仍须加密备份由用户掌控。

---

## 9. 阶段 D：会话记忆策略（必须二选一为主）

### 9.1 方案 D1：客户端权威（当前）

- **行为：** 浏览器继续发送完整 `messages`。
- **服务端：** 不使用 `RunnableWithMessageHistory`，或仅用于内部缓存但 **以客户端为准**。

**优点：** 实现简单，刷新页面前历史一致。  
**缺点：** 请求体随对话变长，成本高；用户篡改可能（一般可接受）。

### 9.2 方案 D2：服务端权威

- **行为：** 客户端只发本轮输入或短窗口；服务端 `session_id` 映射历史。
- **参考：** CloneLLM `memory.py` 进程内 dict + `RunnableWithMessageHistory`。

**优点：** 请求小，便于统一审计。  
**缺点：** 需 **持久化** 与 **会话生命周期**（新对话按钮）；与现前端契约 **不兼容**，必须改版前端。

**纪律：** **禁止** D1 与 D2 同时向模型重复注入同一段历史（会导致重复、角色漂移）。

**建议里程碑：** 在阶段 A/C 完成前保持 D1；D2 作为显式大版本（v2 API 或 `messages` 可选字段）。

---

## 10. 阶段 E：Phase 1 数据炼金（tools/extraction）

**目标：** 将微信等原始导出清洗为 **第一人称、带情感密度、可切块** 的记忆素材（`description.md` Phase 1）。

**推荐步骤：**

1. **脱敏规范：** 定义可保留/必须删除的字段（手机号、第三方全名等）。
2. **流水线：** 解析原始格式 -> 时间线对齐 -> 角色标注 -> LLM 改写为「亲人第一人称」草稿 -> **人工抽检**。
3. 输出：`memories/raw_memories.json`（schema 版本化）+ 供阶段 C 索引的纯文本块列表。

**注意事项：**

- 自动改写仍有幻觉风险，**关键事实**应以原始引用或人工校验表为准。
- 工具放在 `tools/extraction/`，**不要**在对话热路径中自动执行重任务。

**验收：** 至少 1 个合成数据集 + 1 个真实小规模（脱敏）数据集跑通索引与检索。

---

## 11. 阶段 F：Phase 2 人格建模（tools/persona_infer）

**目标：** 从语料估计 Big Five 与语言特征，**生成草稿 `profile.json`**（`description.md` Phase 2）。

**步骤：**

1. 特征提取：统计 + LLM 结构化输出（JSON schema 固定）。
2. 与 `SoulProfile` 对齐字段；低置信度字段标 `null` 或 `confidence` 元数据（若扩展 schema）。
3. **强制人工审核** 后写入包内 `profile.json`。

**注意事项：** 不要自动覆盖用户已手写的 sacred 字段（如姓名、关系）除非用户确认。

---

## 12. 阶段 G：Phase 3 通用适配（MCP / 中间件）

**目标：** 将同一套「拼 prompt + RAG + LLM」作为 **后端服务** 暴露给外部客户端（`core.md` 第 5.3 节）。

**步骤：**

1. 抽象 **内部接口**：`run_turn(input, session_config) -> stream`。
2. MCP：将 `run_turn` 封装为 tool / resource；鉴权与数据路径由用户本地配置。
3. 保持 DigitalTwinPackage **路径级**可迁移，避免绑定单一云厂商。

**注意事项：** 外接客户端可能泄露上下文，需在文档中写明 **风险提示**。

---

## 13. 测试与验收清单（跨阶段）

| 类型 | 内容 |
|------|------|
| 回归 | 关闭所有新开关时，与阶段 0 行为一致 |
| 契约 | `/chat/stream` SSE JSON 字段不变 |
| 安全 | 日志无密钥、无全文记忆、无完整 profile |
| 伦理 | 无检索命中时不编造关键经历；拒答医疗/法律等（按 system_prompts） |
| 性能 | RAG 检索 P95 延迟预算；过大 history 的截断策略 |

---

## 14. 安全、隐私与合规注意事项（汇总）

1. **密钥：** `app_runtime.json` 不入库；CI 使用 example 配置。
2. **包数据：** 用户自备路径；提供「导出/备份」说明。
3. **日志：** 生产默认 INFO 仅元数据；DEBUG 需显式开启且本地。
4. **第三方 API：** 若使用云端模型，提示数据出境与留存政策（产品文档责任）。
5. **心理风险：** 极端情绪场景下，system_prompts 应倾向 **倾听与陪伴**，避免错误治疗暗示（与 `core.md` 行为规范一致）。

---

## 15. 附录：建议的里程碑时间序（可调整）

| 顺序 | 阶段 | 产出 |
|------|------|------|
| 1 | 0 | 稳定基线 |
| 2 | A | 可选包加载 + prompt 合并，默认关闭 |
| 3 | B | chat 服务模块抽离，server 变薄 |
| 4 | C | RAG 索引与检索 + 无命中策略 |
| 5 | E | 离线提取管线（与 C 可部分并行） |
| 6 | F | persona 草稿工具 + 人工审核流 |
| 7 | D2（可选） | 服务端会话 + 前端 v2 |
| 8 | G | MCP / 外部适配 |

---

## 16. 附录：关键文件索引（实施时从这里改）

| 主题 | 路径 |
|------|------|
| HTTP 入口 | `src/server.py` |
| LLM 调用 | `src/liteLLM.py` |
| 包加载 | `src/soulpod/package_loader.py` |
| Prompt | `src/soulpod/prompts/builder.py`、`golden_rules.py` |
| Schema | `src/soulpod/schemas/*` |
| RAG 占位 | `src/soulpod/memory/rag_store.py` |
| 离线工具 | `tools/extraction/`、`tools/persona_infer/` |
| 产品规范 | `Core/core.md`、`Core/description.md` |

---

**文档版本：** 1.0（与仓库目录 scaffold 对齐，后续随 schema 与 API 演进更新 `schema_version` 与第 6 节配置表。）
