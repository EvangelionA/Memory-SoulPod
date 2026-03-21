# 路由（Routes）说明

在 Web 服务里，**路由**指「URL 路径 → 由哪段代码处理」的对应关系。浏览器或前端用不同路径访问时，服务器返回不同内容或执行不同逻辑。

本项目使用 **FastAPI**，在 `src/server.py` 里用装饰器注册路由，例如：

| 方法 | 路径 | 作用 |
|------|------|------|
| GET | `/` | 对话页 `index.html` |
| GET | `/settings` | 设置页 `settings.html` |
| GET | `/status` | 状态灯。本地：HTTP `GET {api_base}/api/tags` 是否 200。远程：HTTP `GET api_base` 是否得到 &lt;500 的响应。 |
| GET | `/api/runtime-config` | 读取当前运行时配置（不含明文 API Key） |
| POST | `/api/runtime-config` | 保存/合并运行时配置到 `config/app_runtime.json` |
| POST | `/chat` | 非流式对话（可选） |
| POST | `/chat/stream` | 流式对话（前端当前使用） |

同源访问时，前端可用相对路径，例如 `fetch("/status")`、`fetch("/api/runtime-config")`。

**与「页面跳转」的关系**：在 HTML 里写 `<a href="/settings">` 时，浏览器会向当前站点请求 `/settings` 这条路由，服务器返回 `settings.html`，这就是「换一个路由 = 换一个页面或接口」。
