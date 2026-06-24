"""FastAPI backend for the Work Engineering Agent."""

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_serializer

from agents import get_agent, list_agents
from llm_router import send_message, list_providers
from knowledge import KnowledgeBase

# Prevent API keys from leaking into logs
logging.getLogger("uvicorn.access").addFilter(
    lambda record: "api_key" not in getattr(record, "getMessage", lambda: "")()
)

app = FastAPI(title="Work Engineering Agent", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
        "font-src https://cdnjs.cloudflare.com; "
        "connect-src 'self'; "
        "img-src 'self' data:"
    )
    return response

kb = KnowledgeBase()


class ChatRequest(BaseModel):
    provider: str
    api_key: str
    model: str
    agent_id: str = "orchestrator"
    messages: list[dict]

    def __repr__(self):
        return f"ChatRequest(provider={self.provider}, model={self.model}, agent_id={self.agent_id}, api_key=***)"

    def __str__(self):
        return self.__repr__()


class ChatResponse(BaseModel):
    reply: str
    sources: list[dict] = []


@app.on_event("startup")
async def startup():
    try:
        kb.load()
        print("Knowledge base loaded.")
    except FileNotFoundError:
        print("WARNING: Knowledge base not built yet. Run: cd backend && python ingest.py")


@app.get("/api/providers")
async def get_providers():
    return list_providers()


@app.get("/api/agents")
async def get_agents():
    return list_agents()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    if not req.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")

    agent = get_agent(req.agent_id)
    system_prompt = agent["system_prompt"]

    # RAG: find relevant knowledge for the latest user message
    sources = []
    last_user_msg = ""
    for msg in reversed(req.messages):
        if msg.get("role") == "user":
            last_user_msg = msg["content"]
            break

    if last_user_msg and kb.index is not None:
        results = kb.search(last_user_msg, top_k=6)
        if results:
            context_parts = []
            for r in results:
                context_parts.append(f"[Source: {r['source']}]\n{r['content']}")
                sources.append({"source": r["source"], "section": r["section"]})

            knowledge_context = "\n\n---\n\n".join(context_parts)
            system_prompt += f"""

## Relevant Knowledge Base Context

Use the following retrieved context to inform your answer. Cite sources when relevant.

{knowledge_context}
"""

    try:
        reply = await send_message(
            provider=req.provider,
            api_key=req.api_key,
            model=req.model,
            messages=req.messages,
            system_prompt=system_prompt,
        )
        return ChatResponse(reply=reply, sources=sources)
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "auth" in error_msg.lower() or "401" in error_msg:
            raise HTTPException(status_code=401, detail="Invalid API key")
        raise HTTPException(status_code=500, detail=error_msg)


# Serve frontend
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
