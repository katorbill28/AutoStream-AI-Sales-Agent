from __future__ import annotations

import json
from typing import Optional

from app.config import GROQ_API_KEY, GROQ_MODEL, USE_GROQ
from app.models import Intent


class GroqHelper:
    def __init__(self) -> None:
        self.client = None
        if not USE_GROQ:
            return
        try:
            from groq import Groq
        except ImportError:
            return
        self.client = Groq(api_key=GROQ_API_KEY)

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def classify_intent(self, message: str) -> Optional[Intent]:
        if not self.client:
            return None

        prompt = (
            "Classify the user's message into exactly one of these labels: "
            "greeting, pricing, policy, feature, lead_capture, general, out_of_scope. "
            "Return JSON only in the form {\"intent\": \"label\"}.\n\n"
            f"Message: {message}"
        )
        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a strict JSON intent classifier."},
                    {"role": "user", "content": prompt},
                ],
            )
            payload = json.loads(response.choices[0].message.content)
            label = payload.get("intent", "")
            return Intent(label)
        except Exception:
            return None

    def build_grounded_answer(self, question: str, context: list[str]) -> Optional[str]:
        if not self.client or not context:
            return None

        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You answer only from the provided AutoStream context. "
                            "Be concise, helpful, and do not invent unavailable details."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Context:\n"
                            + "\n\n".join(context)
                            + "\n\nQuestion:\n"
                            + question
                        ),
                    },
                ],
            )
            return response.choices[0].message.content
        except Exception:
            return None
