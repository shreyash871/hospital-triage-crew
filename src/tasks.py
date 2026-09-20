from crewai import Task
from src.agents import intake_agent, triage_agent, resolver_agent, auditor_agent
from src.schemas import ParsedIntake, TriageDecision, ResolutionPlan, AuditResult


def build_intake_tasks(raw_message: str):

    intake_task = Task(
        description=(
            "Parse this raw patient message into structured fields.\n\n"
            f"MESSAGE:\n\"{raw_message}\"\n\n"
            "Rules:\n"
            "- Copy the concern in the sender's own words.\n"
            "- Leave any field empty if the message does not state it. Never "
            "invent a name, ID, age or symptom.\n"
            "- patient_name is only for the PATIENT's name, and only if the "
            "message names them explicitly.\n"
            "- In red_flag_terms, list any phrase suggesting a possible "
            "emergency (chest pain, numbness, difficulty breathing, bleeding, "
            "loss of consciousness). Extract phrases only — do not judge them.\n"
        ),
        expected_output="A ParsedIntake object with absent fields left null.",
        agent=intake_agent,
        output_pydantic=ParsedIntake,
    )

    triage_task = Task(
        description=(
            "Assign an urgency level and a department.\n\n"
            "Rules:\n"
            "- Chest pain, numbness, difficulty breathing, fast or laboured "
            "breathing, loss of consciousness or heavy bleeding means "
            "EMERGENCY. This applies even if the sender describes it mildly.\n"
            "- Non-empty red_flag_terms means at minimum URGENT.\n"
            "- Missing or ambiguous information is never ROUTINE.\n"
            "- requires_human_review is true for anything not clearly ROUTINE.\n"
            "- State which specific words drove your decision.\n"
            "- Department: if urgency is EMERGENCY the department MUST be "
            "EMERGENCY. Otherwise: bones/joints to ORTHOPEDICS, under-16 to "
            "PEDIATRICS, heart/chest to CARDIOLOGY, else GENERAL_MEDICINE.\n"
            "- The urgency value must be exactly one of these three strings: "
            "EMERGENCY, URGENT, ROUTINE.\n"
        ),
        expected_output="A TriageDecision with reasoning quoting the message.",
        agent=triage_agent,
        context=[intake_task],
        output_pydantic=TriageDecision,
    )

    return [intake_task, triage_task]


def build_resolution_tasks(raw_message, intake, triage, availability, beds):

    resolver_task = Task(
        description=(
            "Decide the concrete action for this case.\n\n"
            f"TRIAGE DECISION:\n{triage.model_dump_json(indent=2)}\n\n"
            f"DOCTOR AVAILABILITY:\n{availability}\n\n"
            f"BED CAPACITY:\n{beds}\n\n"
            "Rules:\n"
            "- EMERGENCY means action ESCALATE_TO_HUMAN with no booking.\n"
            "- If booking_possible is false, action is ADD_TO_WAITLIST.\n"
            "- If slots exist, set action BOOK_APPOINTMENT and copy a "
            "doctor_id and slot_time EXACTLY from the availability data above. "
            "Never invent either one.\n"
            "- Bed status FULL means ESCALATE_TO_HUMAN.\n"
            "- message_to_patient is plain language, no jargon, no diagnosis.\n"
        ),
        expected_output="A ResolutionPlan with the action and its details.",
        agent=resolver_agent,
        output_pydantic=ResolutionPlan,
    )

    audit_task = Task(
        description=(
            "Audit the decisions below against the original message.\n\n"
            f"ORIGINAL MESSAGE:\n\"{raw_message}\"\n\n"
            f"PARSED INTAKE:\n{intake.model_dump_json(indent=2)}\n\n"
            f"TRIAGE DECISION:\n{triage.model_dump_json(indent=2)}\n\n"
            f"DOCTOR AVAILABILITY:\n{availability}\n\n"
            "Rules to check:\n"
            "1. EMERGENCY urgency must have action ESCALATE_TO_HUMAN.\n"
            "2. Non-empty red_flag_terms must produce at least URGENT.\n"
            "3. EMERGENCY urgency must have department EMERGENCY.\n"
            "4. Any slot_time must appear in the availability data above.\n"
            "5. Every value in PARSED INTAKE must trace back to the original "
            "message. Check only the PARSED INTAKE fields — do NOT treat "
            "symptoms named in the reasoning text as invented details, since "
            "reasoning often lists symptoms to explain their absence.\n\n"
            "List every rule broken. approved is false if there is even one. "
            "If urgency was too low, set corrected_urgency — raise only, "
            "never lower.\n"
        ),
        expected_output="An AuditResult with violations and notes.",
        agent=auditor_agent,
        context=[resolver_task],
        output_pydantic=AuditResult,
    )

    return [resolver_task, audit_task]