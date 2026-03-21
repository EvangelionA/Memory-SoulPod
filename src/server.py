"""
SoulPod HTTP API: 供前端 index.html 调用的聊天接口。
入口: python -m src.core
访问: http://localhost:8000/  设置页: http://localhost:8000/settings
"""
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from src.liteLLM import DEFAULT_API_BASE, DEFAULT_MODEL, ollama_chat, ollama_chat_stream

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config" / "app_runtime.json"

DEFAULT_RUNTIME: Dict[str, str] = {
    "model": DEFAULT_MODEL,
    "api_base": DEFAULT_API_BASE,
    "system_prompt": "",
    "api_key": "",
}

STATUS_HTTP_TIMEOUT_SEC = 5

app = FastAPI(title="SoulPod API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_runtime_config() -> Dict[str, str]:
    """Read merged runtime config from disk."""
    cfg = dict(DEFAULT_RUNTIME)
    if CONFIG_FILE.is_file():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cfg.update({k: str(v) if v is not None else "" for k, v in data.items() if k in DEFAULT_RUNTIME})
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def save_runtime_config(cfg: Dict[str, str]) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    out = {k: cfg.get(k, DEFAULT_RUNTIME[k]) for k in DEFAULT_RUNTIME}
    CONFIG_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


def public_runtime_config() -> Dict[str, Any]:
    """Safe for GET: no raw api_key."""
    c = get_runtime_config()
    return {
        "model": c["model"],
        "api_base": c["api_base"],
        "system_prompt": c["system_prompt"],
        "api_key_set": bool((c.get("api_key") or "").strip()),
    }


def _messages_with_system(messages: List[dict], system_prompt: str) -> List[dict]:
    sp = (system_prompt or "").strip()
    if not sp:
        return list(messages)
    return [{"role": "system", "content": sp}] + list(messages)


def _litellm_extras(cfg: Dict[str, str]) -> Optional[Dict[str, Any]]:
    k = (cfg.get("api_key") or "").strip()
    if k:
        return {"api_key": k}
    return None


def _is_local_ollama_runtime(cfg: Dict[str, str]) -> bool:
    """True when LiteLLM model is Ollama (local)."""
    return (cfg.get("model") or "").strip().lower().startswith("ollama/")


def _check_ollama_http(api_base: str) -> bool:
    """Ollama up iff GET /api/tags returns HTTP 200."""
    base = (api_base or DEFAULT_API_BASE).rstrip("/")
    try:
        req = urllib.request.Request(f"{base}/api/tags")
        with urllib.request.urlopen(req, timeout=STATUS_HTTP_TIMEOUT_SEC) as r:
            return r.status == 200
    except Exception:
        return False


def _check_web_api_http(api_base: str) -> bool:
    """Remote base URL reachable: any HTTP response with status < 500 counts as up."""
    base = (api_base or "").strip().rstrip("/")
    if not base.startswith("http"):
        return False
    try:
        req = urllib.request.Request(base, method="GET")
        with urllib.request.urlopen(req, timeout=STATUS_HTTP_TIMEOUT_SEC) as r:
            return r.status < 500
    except urllib.error.HTTPError as e:
        return e.code < 500
    except Exception:
        return False


def _status_connected_http(cfg: Dict[str, str]) -> bool:
    if _is_local_ollama_runtime(cfg):
        return _check_ollama_http(cfg.get("api_base") or DEFAULT_API_BASE)
    return _check_web_api_http(cfg.get("api_base") or "")


class ChatRequest(BaseModel):
    messages: list[dict]


class ChatResponse(BaseModel):
    reply: str


class RuntimeConfigPatch(BaseModel):
    model: Optional[str] = None
    api_base: Optional[str] = None
    system_prompt: Optional[str] = None
    api_key: Optional[str] = None


@app.get("/status")
def status():
    cfg = get_runtime_config()
    local = _is_local_ollama_runtime(cfg)
    connected = _status_connected_http(cfg)
    return {
        "mode": "local" if local else "web",
        "connected": connected,
        "ollama": connected if local else False,
    }


@app.get("/api/runtime-config")
def get_runtime_config_api():
    return public_runtime_config()


@app.post("/api/runtime-config")
def post_runtime_config(patch: RuntimeConfigPatch):
    cur = get_runtime_config()
    data = patch.model_dump(exclude_unset=True)
    for k, v in data.items():
        if k in DEFAULT_RUNTIME and v is not None:
            cur[k] = v
    save_runtime_config(cur)
    return public_runtime_config()


@app.get("/")
def index():
    index_path = ROOT / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail=f"index.html not found at {index_path}")
    return FileResponse(str(index_path), media_type="text/html; charset=utf-8")


@app.get("/settings")
def settings_page():
    path = ROOT / "settings.html"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="settings.html not found")
    return FileResponse(str(path), media_type="text/html; charset=utf-8")


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")
    cfg = get_runtime_config()
    msgs = _messages_with_system(req.messages, cfg["system_prompt"])
    extras = _litellm_extras(cfg)
    try:
        reply = await ollama_chat(
            messages=msgs,
            model=cfg["model"] or DEFAULT_MODEL,
            api_base=cfg["api_base"] or DEFAULT_API_BASE,
            stream=False,
            extra_params=extras,
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


async def _sse_stream(messages: list):
    cfg = get_runtime_config()
    msgs = _messages_with_system(messages, cfg["system_prompt"])
    extras = _litellm_extras(cfg)
    try:
        async for delta in ollama_chat_stream(
            messages=msgs,
            model=cfg["model"] or DEFAULT_MODEL,
            api_base=cfg["api_base"] or DEFAULT_API_BASE,
            extra_params=extras,
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
