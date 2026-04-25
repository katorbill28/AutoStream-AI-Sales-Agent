from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Intent(str, Enum):
    GREETING = "greeting"
    PRICING = "pricing"
    POLICY = "policy"
    FEATURE = "feature"
    LEAD_CAPTURE = "lead_capture"
    GENERAL = "general"
    OUT_OF_SCOPE = "out_of_scope"


class LeadStatus(str, Enum):
    UNQUALIFIED = "unqualified"
    DISCOVERING = "discovering"
    QUALIFIED = "qualified"
    CAPTURED = "captured"


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class LeadRecord(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    use_case: Optional[str] = None
    team_size: Optional[str] = None
    budget: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    intent: Intent
    lead_status: LeadStatus
    retrieved_context: List[str] = Field(default_factory=list)
    lead: LeadRecord = Field(default_factory=LeadRecord)


class ConversationState(BaseModel):
    session_id: str
    history: List[str] = Field(default_factory=list)
    lead_status: LeadStatus = LeadStatus.UNQUALIFIED
    lead: LeadRecord = Field(default_factory=LeadRecord)

