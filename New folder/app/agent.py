from __future__ import annotations

import re
from typing import Dict, List

from app.knowledge_base import KnowledgeBase
from app.lead_store import LeadStore
from app.llm import GroqHelper
from app.models import ChatResponse, ConversationState, Intent, LeadRecord, LeadStatus


class AutoStreamAgent:
    def __init__(self, knowledge_base: KnowledgeBase, lead_store: LeadStore) -> None:
        self.knowledge_base = knowledge_base
        self.lead_store = lead_store
        self.llm = GroqHelper()
        self.sessions: Dict[str, ConversationState] = {}

    def get_state(self, session_id: str) -> ConversationState:
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationState(session_id=session_id)
        return self.sessions[session_id]

    def classify_intent(self, message: str) -> Intent:
        llm_intent = self.llm.classify_intent(message)
        if llm_intent is not None:
            return llm_intent

        text = message.lower()
        if any(word in text for word in ["hi", "hello", "hey"]) and len(text.split()) <= 4:
            return Intent.GREETING
        if any(word in text for word in ["price", "pricing", "cost", "plan", "plans"]):
            return Intent.PRICING
        if any(word in text for word in ["policy", "refund", "cancel", "security", "sla", "support"]):
            return Intent.POLICY
        if any(word in text for word in ["feature", "features", "integrat", "automation", "crm", "dashboard"]):
            return Intent.FEATURE
        if any(
            phrase in text
            for phrase in [
                "book a demo",
                "talk to sales",
                "get started",
                "sign up",
                "contact me",
                "interested",
                "buy",
                "purchase",
            ]
        ):
            return Intent.LEAD_CAPTURE
        if any(word in text for word in ["autostream", "product", "platform"]):
            return Intent.GENERAL
        return Intent.GENERAL

    def _extract_lead_details(self, state: ConversationState, message: str) -> None:
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", message)
        if email_match:
            state.lead.email = email_match.group(0)

        name_match = re.search(r"(?:i am|i'm|my name is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", message, re.IGNORECASE)
        if name_match and not state.lead.name:
            state.lead.name = name_match.group(1).strip()

        company_match = re.search(r"(?:company|from)\s+([A-Za-z0-9& .-]{2,})", message, re.IGNORECASE)
        if company_match and not state.lead.company:
            state.lead.company = company_match.group(1).strip(" .")

        if any(word in message.lower() for word in ["use case", "need", "looking for", "want to"]):
            state.lead.use_case = state.lead.use_case or message.strip()

        team_match = re.search(r"(\d+\s*(?:people|users|agents|team members))", message, re.IGNORECASE)
        if team_match:
            state.lead.team_size = team_match.group(1)

        budget_match = re.search(r"(\$?\d[\d,]*(?:\s*/\s*month|\s*per month|\s*monthly)?)", message, re.IGNORECASE)
        if budget_match:
            state.lead.budget = budget_match.group(1)

    @staticmethod
    def _missing_fields(lead: LeadRecord) -> List[str]:
        required = {
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "use_case": lead.use_case,
        }
        return [field for field, value in required.items() if not value]

    def _should_qualify(self, state: ConversationState, intent: Intent) -> bool:
        return intent == Intent.LEAD_CAPTURE or state.lead_status in {
            LeadStatus.DISCOVERING,
            LeadStatus.QUALIFIED,
        }

    def _build_context_answer(self, intent: Intent, message: str) -> tuple[str, List[str]]:
        retrieved = self.knowledge_base.retrieve(message)
        snippets = [chunk.text for chunk in retrieved]
        if not snippets:
            return (
                "I can help with AutoStream pricing, features, and policies. Ask about plans, onboarding, integrations, or support terms.",
                [],
            )

        grounded_answer = self.llm.build_grounded_answer(message, snippets)
        if grounded_answer:
            return grounded_answer, snippets

        intro = {
            Intent.PRICING: "Here's the most relevant pricing information I found:",
            Intent.POLICY: "Here are the most relevant policy details I found:",
            Intent.FEATURE: "Here are the most relevant feature details I found:",
        }.get(intent, "Here's what I found in the AutoStream knowledge base:")

        answer = intro + "\n\n" + "\n\n".join(f"- {snippet}" for snippet in snippets)
        return answer, snippets

    def respond(self, session_id: str, message: str) -> ChatResponse:
        state = self.get_state(session_id)
        state.history.append(f"user: {message}")
        intent = self.classify_intent(message)
        self._extract_lead_details(state, message)

        if self._should_qualify(state, intent):
            state.lead_status = LeadStatus.DISCOVERING
            missing = self._missing_fields(state.lead)
            if missing:
                prompts = {
                    "name": "What name should I use for the lead?",
                    "email": "What is the best work email for follow-up?",
                    "company": "Which company are you with?",
                    "use_case": "What would you like AutoStream to help your team automate?",
                }
                response_text = prompts[missing[0]]
                state.history.append(f"assistant: {response_text}")
                return ChatResponse(
                    session_id=session_id,
                    response=response_text,
                    intent=intent,
                    lead_status=state.lead_status,
                    lead=state.lead,
                )

            state.lead_status = LeadStatus.QUALIFIED
            self.lead_store.save(session_id, state.lead)
            state.lead_status = LeadStatus.CAPTURED
            response_text = (
                "You're all set. I've captured your lead for the AutoStream team.\n\n"
                f"Name: {state.lead.name}\n"
                f"Email: {state.lead.email}\n"
                f"Company: {state.lead.company}\n"
                f"Use case: {state.lead.use_case}"
            )
            state.history.append(f"assistant: {response_text}")
            return ChatResponse(
                session_id=session_id,
                response=response_text,
                intent=intent,
                lead_status=state.lead_status,
                lead=state.lead,
            )

        if intent == Intent.GREETING:
            response_text = (
                "I can help with AutoStream pricing, features, policies, and demo requests. "
                "Tell me what you want to learn or if you want me to capture your details for sales."
            )
            state.history.append(f"assistant: {response_text}")
            return ChatResponse(
                session_id=session_id,
                response=response_text,
                intent=intent,
                lead_status=state.lead_status,
                lead=state.lead,
            )

        response_text, snippets = self._build_context_answer(intent, message)
        state.history.append(f"assistant: {response_text}")
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            intent=intent,
            lead_status=state.lead_status,
            retrieved_context=snippets,
            lead=state.lead,
        )
