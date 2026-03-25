"""
MediAssist — Async FastAPI backend
Stateless: no sessions, no history storage
Every request is fully independent
"""

import os
import httpx
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import List
from pydantic import validator
# ── Load .env ────────────────────────────────────────────────────────────────
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
APP_HOST     = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT     = int(os.getenv("APP_PORT", 8000))
DEBUG        = os.getenv("DEBUG", "false").lower() == "true"

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set in the .env file")

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are MediAssist, a medical-only AI assistant.

You ONLY answer questions related to:
- Symptoms, diseases, and medical conditions
- Medications and treatments
- Mental health and wellness
- Nutrition, diet, and healthy lifestyle
- First aid and emergency guidance
- Preventive care and vaccinations

If the user asks ANYTHING outside of medical and health topics, respond with exactly:
"I'm MediAssist, a medical-only assistant. I can only help with health and medical questions. Please ask me something related to your health!"

Do NOT answer questions about technology, cars, politics, entertainment, coding, or any non-medical topic — no exceptions.

Important rules:
- NEVER diagnose definitively — always recommend consulting a doctor
- If user describes an emergency, immediately advise calling 112 or local emergency services
- Keep responses clear and easy to understand
- Always recommend professional medical consultation for serious symptoms"""


# ── Shared async HTTP client (reused across requests) ─────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(timeout=60.0)
    yield
    await app.state.http_client.aclose()


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MediAssist API",
    description="Stateless async medical AI chatbot powered by Groq",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if DEBUG else None,   # hide docs in production
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to your domain in production
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ── Schemas ───────────────────────────────────────────────────────────────────


class Message(BaseModel):
    role: str
    content: str

    @validator("role")
    def role_must_be_valid(cls, v):
        if v not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")
        return v

    @validator("content")
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError("content cannot be empty")
        return v[:4000]

class ChatRequest(BaseModel):
    messages: List[Message]
class ChatResponse(BaseModel):
    reply: str


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """EC2 load-balancer / uptime health check endpoint."""
    return {"status": "ok", "model": GROQ_MODEL}


@app.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest):
    """
    Stateless chat endpoint.
    Receives the conversation turns from the client,
    prepends the system prompt, calls Groq, returns the reply.
    Nothing is stored server-side.
    """
    payload = {
        "model": GROQ_MODEL,
        "max_tokens": 1024,
        "temperature": 0.6,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            *[m.model_dump() for m in body.messages],
        ],
    }

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = await app.state.http_client.post(
            GROQ_API_URL, json=payload, headers=headers
        )
        response.raise_for_status()
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return ChatResponse(reply=reply)

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Groq API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Serve static frontend ─────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def index():
    return FileResponse("static/index.html")


# ── Dev runner ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=DEBUG)
