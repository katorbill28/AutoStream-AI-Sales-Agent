from __future__ import annotations

from fastapi import FastAPI

from app.agent import AutoStreamAgent
from app.config import KNOWLEDGE_DIR, LEADS_FILE
from app.knowledge_base import KnowledgeBase
from app.lead_store import LeadStore
from app.models import ChatRequest, ChatResponse


app = FastAPI(title="AutoStream Lead Agent", version="1.0.0")

knowledge_base = KnowledgeBase(KNOWLEDGE_DIR)
lead_store = LeadStore(LEADS_FILE)
agent = AutoStreamAgent(knowledge_base=knowledge_base, lead_store=lead_store)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    return agent.respond(payload.session_id, payload.message)

