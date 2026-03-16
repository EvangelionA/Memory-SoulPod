"""
SoulPod HTTP API: 供前端 index.html 调用的聊天接口。
在项目根目录执行: python -m uvicorn src.server:app --reload --host 0.0.0.0 --port 8000
浏览器访问 http://localhost:8000/ 即可使用对话页。
"""
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from src.liteLLM import ollama_chat, ollama_chat_stream

# 项目根目录（假定在根目录启动 uvicorn）
ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="SoulPod API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    messages: list[dict]  # [{"role": "user"|"assistant", "content": "..."}, ...]


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
def index():
    """返回前端页面，便于同源访问 /chat，无需单独起静态服务。"""
    index_path = ROOT / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail=f"index.html not found at {index_path}")
    return FileResponse(str(index_path), media_type="text/html; charset=utf-8")


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")
    try:
        reply = await ollama_chat(
            messages=req.messages,
            model="ollama/qwen3:8b",
            api_base="http://localhost:11434",
            stream=False,
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


async def _sse_stream(messages: list):
    """SSE 流：每块 data 为 JSON {"delta": "..."}，结束时 {"done": true}"""
    try:
        async for delta in ollama_chat_stream(
            messages=messages,
            model="ollama/qwen3:8b",
            api_base="http://localhost:11434",
        ):
            yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")
    return StreamingResponse(
        _sse_stream(req.messages),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
