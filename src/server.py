"""
SoulPod HTTP API: 供前端 index.html 调用的聊天接口。
入口: python -m src.core
访问: http://localhost:8000/  设置页: http://localhost:8000/settings
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from src.liteLLM import DEFAULT_API_BASE, DEFAULT_MODEL, ollama_chat, ollama_chat_stream
from tools.prompt import LLM_CONNECTION_VERIFY_PROMPT

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config" / "app_runtime.json"

DEFAULT_RUNTIME: Dict[str, str] = {
    "model": DEFAULT_MODEL,
    "api_base": DEFAULT_API_BASE,
    "system_prompt": "",
    "api_key": "",
}

STATUS_LLM_TIMEOUT_SEC = 12.0
STATUS_LLM_MAX_TOKENS = 64
_web_status_cache: Optional[bool] = None  # web mode: filled by GET /status?refresh=1; cleared on config save

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


def _parse_llm_verify_reply(text: str) -> bool:
    """TRUE/FALSE word match; last match wins."""
    matches = re.findall(r"\b(TRUE|FALSE)\b", (text or "").upper())
    if not matches:
        return False
    return matches[-1] == "TRUE"


async def _status_connected_via_llm(cfg: Dict[str, str]) -> bool:
    """LLM probe using LLM_CONNECTION_VERIFY_PROMPT."""
    model = (cfg.get("model") or DEFAULT_MODEL).strip()
    api_base = (cfg.get("api_base") or DEFAULT_API_BASE).strip()
    if not model:
        return False
    if not _is_local_ollama_runtime(cfg):
        if not api_base.startswith("http"):
            return False

    extras = dict(_litellm_extras(cfg) or {})
    extras.setdefault("timeout", STATUS_LLM_TIMEOUT_SEC)
    extras.setdefault("max_tokens", STATUS_LLM_MAX_TOKENS)

    messages = [{"role": "user", "content": LLM_CONNECTION_VERIFY_PROMPT}]
    try:
        reply = await ollama_chat(
            messages=messages,
            model=model,
            api_base=api_base or DEFAULT_API_BASE,
            stream=False,
            extra_params=extras,
        )
        return _parse_llm_verify_reply(reply)
    except Exception:
        return False


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
async def status(refresh: bool = False):
    cfg = get_runtime_config()
    local = _is_local_ollama_runtime(cfg)
    global _web_status_cache

    if local or refresh:
        connected = await _status_connected_via_llm(cfg)
        if not local and refresh:
            _web_status_cache = connected
    else:
        connected = _web_status_cache if _web_status_cache is not None else False

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
    global _web_status_cache
    cur = get_runtime_config()
    data = patch.model_dump(exclude_unset=True)
    for k, v in data.items():
        if k in DEFAULT_RUNTIME and v is not None:
            cur[k] = v
    save_runtime_config(cur)
    _web_status_cache = None
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
