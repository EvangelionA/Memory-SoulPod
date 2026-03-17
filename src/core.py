"""
SoulPod 入口：python -m src.core 启动 Web 服务
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
