from pathlib import Path

from app.agent import AutoStreamAgent
from app.knowledge_base import KnowledgeBase
from app.lead_store import LeadStore
from app.models import Intent, LeadStatus


def build_agent(tmp_path: Path) -> AutoStreamAgent:
    kb = KnowledgeBase(Path("data/knowledge_base"))
    store = LeadStore(tmp_path / "leads.jsonl")
    return AutoStreamAgent(kb, store)


def test_pricing_intent_returns_context(tmp_path: Path) -> None:
    agent = build_agent(tmp_path)
    response = agent.respond("pricing-session", "What are your pricing plans?")
    assert response.intent == Intent.PRICING
    assert response.retrieved_context
    assert "pricing" in response.response.lower()


def test_policy_intent_returns_policy_context(tmp_path: Path) -> None:
    agent = build_agent(tmp_path)
    response = agent.respond("policy-session", "Tell me about your refund and cancellation policy.")
    assert response.intent == Intent.POLICY
    assert any("Refunds" in chunk or "canceled" in chunk for chunk in response.retrieved_context)


def test_lead_capture_flow(tmp_path: Path) -> None:
    agent = build_agent(tmp_path)
    first = agent.respond("lead-session", "I'm interested in booking a demo.")
    second = agent.respond("lead-session", "My name is Riya Kapoor.")
    third = agent.respond("lead-session", "riya@acme.com")
    fourth = agent.respond("lead-session", "I am from Acme Robotics.")
    fifth = agent.respond("lead-session", "We want to automate inbound sales qualification.")

    assert first.lead_status == LeadStatus.DISCOVERING
    assert fifth.lead_status == LeadStatus.CAPTURED
    assert "captured your lead" in fifth.response.lower()
