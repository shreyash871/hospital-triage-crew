from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class Urgency(str, Enum):
    EMERGENCY = "EMERGENCY"
    URGENT = "URGENT"
    ROUTINE = "ROUTINE"


class Department(str, Enum):
    CARDIOLOGY = "CARDIOLOGY"
    ORTHOPEDICS = "ORTHOPEDICS"
    PEDIATRICS = "PEDIATRICS"
    GENERAL_MEDICINE = "GENERAL_MEDICINE"
    EMERGENCY = "EMERGENCY"


class Action(str, Enum):
    BOOK_APPOINTMENT = "BOOK_APPOINTMENT"
    ESCALATE_TO_HUMAN = "ESCALATE_TO_HUMAN"
    ADD_TO_WAITLIST = "ADD_TO_WAITLIST"


class ParsedIntake(BaseModel):
    """Structured form of a raw patient message."""
    patient_name: Optional[str] = Field(None, description="Name if stated")
    patient_id: Optional[str] = Field(None, description="Hospital ID if stated")
    reported_concern: str = Field(..., description="The complaint in the sender's own words")
    duration: Optional[str] = Field(None, description="How long it has been going on")
    requested_timing: Optional[str] = Field(None, description="When they want to be seen")
    red_flag_terms: List[str] = Field(
        default_factory=list,
        description="Phrases suggesting a possible emergency"
    )


class TriageDecision(BaseModel):
    """Urgency and routing. Never a diagnosis."""
    urgency: Urgency
    department: Department
    reasoning: str = Field(..., description="Why this urgency was assigned")
    requires_human_review: bool = Field(
        ..., description="True for anything not clearly routine"
    )
    
class ResolutionPlan(BaseModel):
    """What the ops desk should actually do."""
    action: Action
    department: Department
    doctor_id: Optional[str] = Field(None, description="Assigned doctor, if booking")
    slot_time: Optional[str] = Field(None, description="Proposed appointment time")
    escalation_reason: Optional[str] = Field(
        None, description="Why a human must handle this"
    )
    message_to_patient: str = Field(..., description="Plain-language reply to send")


class AuditResult(BaseModel):
    """Safety gate. The last thing before anything is acted on."""
    approved: bool
    violations: List[str] = Field(
        default_factory=list, description="Rules broken, if any"
    )
    corrected_urgency: Optional[Urgency] = Field(
        None, description="Set only if the auditor overrides the triage call"
    )
    audit_notes: str