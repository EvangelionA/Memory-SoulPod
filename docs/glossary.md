# SoulPod 术语表 (Glossary)

固定团队与文档用语，与 `Core/description.md`、`docs/implementation_pipeline.md` 一致。

| 术语 (EN) | 中文 | 含义 |
|-----------|------|------|
| **Package** | 载体包 / DigitalTwinPackage | 符合 `Core/` 规范的一组目录与文件（`profile.json`、`system_prompts.txt`、`config.json`、`memories/` 等），可迁移、可备份的数字资产根目录。 |
| **Profile** | 人物画像 | 结构化描述「他是谁」：身份、关系、人格与语言风格等，主文件为包内 `profile.json`；对应三位一体中的 **User Profile**。 |
| **RAG** | 检索增强生成 / 长期记忆 | 从 `memories/` 向量库或文本块中检索与当前问题相关的摘录，注入模型上下文；对应三位一体中的 **RAG Memory**。 |
| **Runtime config** | 运行时配置 | 服务启动后读取的机器级配置，当前为项目根下 `config/app_runtime.json`（**不入库**），用于模型 ID、`api_base`、`system_prompt`、API Key 等；示例见 `config/app_runtime.example.json`。 |

**相关路径：** `packages/` 下为示例或本地载体；`src/soulpod/` 为加载与编排代码（尚未全部接入 HTTP 时仍以本文档与 `implementation_pipeline.md` 为准）。
