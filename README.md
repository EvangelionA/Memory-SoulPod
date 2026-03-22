# Memory-SoulPod

> *见字如面，温润如初。*

一个通过 AI 技术为逝去亲人构建永恒数字载体的开源项目。

## 简介

Memory-SoulPod 旨在通过"人格解耦"技术，将亲人的记忆、性格和语气从具体的 AI 模型中剥离，封装为标准化的数字资产包。让用户能够与已故亲人进行日常对话，延续情感的纽带。

## 核心特性

- **人格解耦**：将人的特质（记忆、性格、语气）与 AI 模型分离
- **数字资产化**：封装为可永久保存、跨平台迁移的标准化文件包
- **三位一体架构**：
  - 长期记忆 (RAG Memory)
  - 人物画像 (User Profile)
  - 行为规范 (System Prompts)

## 项目结构

```
Memory-SoulPod/
├── Core/                    # 核心文档（愿景与 DigitalTwinPackage 规范）
│   ├── core.md
│   └── description.md
├── packages/                # 数字载体包目录（示例见 packages/_template，勿提交真实隐私数据）
├── src/
│   ├── server.py            # FastAPI（当前前后端对接入口）
│   ├── liteLLM.py
│   ├── core.py              # 启动入口 python -m src.core
│   └── soulpod/             # 领域引擎（加载包、组 prompt、RAG/会话占位；尚未接入 HTTP）
├── tools/                   # 离线工具（提取、人格推断等子包）
├── config/                  # 运行时配置（见 config/README.md；app_runtime.json 不入库）
├── docs/                    # 文档（含 docs/package_layout.md、docs/glossary.md）
├── examples/
└── README.md
```

## 环境要求

- **Python** 3.10 或更高（开发与运行推荐 3.10+）。
- **依赖**：见仓库根目录 `requirements.txt`（主要包含 FastAPI、Uvicorn、LiteLLM、Pydantic 等）；安装：`pip install -r requirements.txt`。
- **术语**：Package（载体包）、Profile（人物画像）、RAG（长期记忆检索）、Runtime config（`config/app_runtime.json`）— 见 [`docs/glossary.md`](docs/glossary.md)。

## 快速开始

```bash
# 克隆项目
git clone https://github.com/your-repo/Memory-SoulPod.git
cd Memory-SoulPod

# 安装依赖
pip install -r requirements.txt

# 0. 本地运行时配置（可选：复制示例后编辑，或通过 /settings 页面保存）
#    copy config\app_runtime.example.json config\app_runtime.json   # Windows
#    cp config/app_runtime.example.json config/app_runtime.json        # Unix
#    app_runtime.json 已被 .gitignore 忽略，勿提交真实 API Key

# 1. 启动本地模型（若使用 Ollama：安装 Ollama 并拉取与配置一致的模型，例如示例中的 qwen3:8b）
#    ollama pull qwen3:8b

# 2. 启动 Web 服务（在项目根目录执行）
python -m src.core

# 3. 浏览器打开 http://localhost:8000/ 或 http://127.0.0.1:8000/

# 可选：设置页 http://localhost:8000/settings（模型、API、角色提示词等写入 `config/app_runtime.json`，见 `config/app_runtime.example.json`）

# 路由说明见 `docs/routes.md`

## 核心准则

- **拒绝幻觉**：宁肯表达模糊印象，严禁编造关键人生经历
- **去 AI 化**：不提及"模型"或"算法"，保持特定人的身份
- **隐私至上**：优先保护数据的本地化与私密性

## 开发路线

1. **数据炼金** - 将碎片化聊天记录清洗为记忆块
2. **灵魂建模** - 自动化提取性格参数与语言模式
3. **无缝陪伴** - 跨平台挂载到主流 AI 助手

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
