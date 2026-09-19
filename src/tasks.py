from crewai import Task
from src.agents import intake_agent, triage_agent, resolver_agent, auditor_agent
from src.schemas import ParsedIntake, TriageDecision, ResolutionPlan, AuditResult


def build_tasks(raw_message: str):

    intake_task = Task(
        description=(
            "Parse this raw patient message into structured fields.\n\n"
            f"MESSAGE:\n\"{raw_message}\"\n\n"
            "Rules:\n"
            "- Copy the concern in the sender's own words. Do not rephrase it "
            "into medical terms.\n"
            "- If a patient ID (format P####) is present, use the "
            "lookup_patient tool to confirm it. If no ID is present, do NOT "
            "use the tool.\n"
            "- Leave any field empty if the message does not state it. Never "
            "invent a name, ID, age or symptom.\n"
            "- In red_flag_terms, list any phrase suggesting a possible "
            "emergency (e.g. chest pain, numbness, difficulty breathing, "
            "bleeding, loss of consciousness). Extract the phrases only — do "
            "not judge how serious they are."
        ),
        expected_output=(
            "A ParsedIntake object. Every field present in the message is "
            "filled; every field absent from it is null or an empty list."
        ),
        agent=intake_agent,
        output_pydantic=ParsedIntake,
    )

    triage_task = Task(
        description=(
            "Assign an urgency level and a department based on the parsed "
            "intake.\n\n"
            "Rules:\n"
            "- If red_flag_terms is non-empty, urgency is at minimum URGENT.\n"
            "- Chest pain, numbness, difficulty breathing, loss of "
            "consciousness or heavy bleeding means EMERGENCY.\n"
            "- If key information is missing or the case is ambiguous, do NOT "
            "classify it ROUTINE.\n"
            "- Set requires_human_review to true for anything that is not "
            "clearly ROUTINE.\n"
            "- In reasoning, state which specific words in the message drove "
            "your decision.\n"
            "- Route to a department: heart/chest to CARDIOLOGY, bones/joints "
            "to ORTHOPEDICS, under-16 to PEDIATRICS, anything immediately "
            "life-threatening to EMERGENCY, otherwise GENERAL_MEDICINE."
        ),
        expected_output=(
            "A TriageDecision with urgency, department, reasoning that quotes "
            "the message, and requires_human_review set."
        ),
        agent=triage_agent,
        context=[intake_task],
        output_pydantic=TriageDecision,
    )

    resolver_task = Task(
        description=(
            "Decide the concrete action for this case.\n\n"
            "Rules:\n"
            "- If urgency is EMERGENCY: action is ESCALATE_TO_HUMAN. Do not "
            "book anything. Do not call the booking tool.\n"
            "- Otherwise call get_doctor_schedule for the department.\n"
            "- If booking_possible is false, action is ADD_TO_WAITLIST.\n"
            "- If slots exist, pick one and call create_booking. The slot_time "
            "must be copied exactly from the schedule result.\n"
            "- For any inpatient concern, check bed availability first. A FULL "
            "department means ESCALATE_TO_HUMAN.\n"
            "- Write message_to_patient in plain language, no medical jargon, "
            "no diagnosis, no reassurance about their condition."
        ),
        expected_output=(
            "A ResolutionPlan with the action taken, and either booking "
            "details or an escalation reason."
        ),
        agent=resolver_agent,
        context=[intake_task, triage_task],
        output_pydantic=ResolutionPlan,
    )

    audit_task = Task(
        description=(
            "Audit the triage decision and resolution plan against the "
            "original message.\n\n"
            f"ORIGINAL MESSAGE:\n\"{raw_message}\"\n\n"
            "Check every rule:\n"
            "1. An EMERGENCY case must have action ESCALATE_TO_HUMAN.\n"
            "2. A non-empty red_flag_terms must produce at least URGENT.\n"
            "3. Any booked slot_time must exist in get_doctor_schedule for "
            "that department. Verify it with the tool.\n"
            "4. No patient detail may appear that the original message did "
            "not contain.\n\n"
            "List every rule broken in violations. Set approved false if there "
            "is even one. If urgency was set too low, put the correct value in "
            "corrected_urgency — you may raise it, never lower it."
        ),
        expected_output=(
            "An AuditResult with approved, any violations found, an optional "
            "corrected_urgency, and audit notes."
        ),
        agent=auditor_agent,
        context=[intake_task, triage_task, resolver_task],
        output_pydantic=AuditResult,
    )

    return [intake_task, triage_task, resolver_task, audit_task]