"""
SoulPod HTTP API: 供前端 index.html 调用的聊天接口。
入口: python -m src.core
访问: http://localhost:8000/
"""
import json
import urllib.request
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from src.liteLLM import ollama_chat, ollama_chat_stream

ROOT = Path(__file__).resolve().parent.parent
OLLAMA_MODEL = "ollama/qwen3:8b"
OLLAMA_BASE = "http://localhost:11434"

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


def _check_ollama() -> bool:
    """检测 Ollama 是否可连接"""
    try:
        req = urllib.request.Request(f"{OLLAMA_BASE}/api/tags")
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


@app.get("/status")
def status():
    """返回 Ollama 连接状态，供前端 STATUS 显示"""
    return {"ollama": _check_ollama()}


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
            model=OLLAMA_MODEL,
            api_base=OLLAMA_BASE,
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
            model=OLLAMA_MODEL,
            api_base=OLLAMA_BASE,
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
