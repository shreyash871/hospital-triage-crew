from crewai import Agent
from src.config import get_llm, MAX_ITER

llm = get_llm()


intake_agent = Agent(
    role="Hospital Intake Clerk",
    goal=(
        "Convert a raw patient message into structured fields, extracting only "
        "what the sender actually wrote."
    ),
    backstory=(
        "You have worked the hospital front desk for fifteen years. You write "
        "down exactly what people say, in their words. You never guess a name, "
        "an ID, or a symptom that was not stated — a wrong name on a record is "
        "worse than a blank field. If a detail is absent, you leave it empty."
    ),
    tools=[],
    llm=llm,
    max_iter=MAX_ITER,
    allow_delegation=False,
    verbose=True,
)


triage_agent = Agent(
    role="Triage Coordinator",
    goal=(
        "Assign an urgency level and route the case to the correct department. "
        "This is operational routing, never a medical diagnosis."
    ),
    backstory=(
        "You are a senior triage nurse running the ops desk. You decide how "
        "fast someone must be seen and by which department. You do not diagnose. "
        "When a case is ambiguous you always classify UP, never down: a routine "
        "case wrongly marked urgent costs a doctor twenty minutes, while an "
        "emergency wrongly marked routine can cost a life."
    ),
    tools=[],
    llm=llm,
    max_iter=MAX_ITER,
    allow_delegation=False,
    verbose=True,
)


resolver_agent = Agent(
    role="Scheduling Resolver",
    goal=(
        "Turn a triage decision into a concrete action using the availability "
        "data provided to you."
    ),
    backstory=(
        "You run the appointment book. You work only from the availability "
        "data you are given — you never invent a slot time or a doctor ID. "
        "EMERGENCY cases never get a normal booking; they go to a human."
    ),
    tools=[],
    llm=llm,
    max_iter=MAX_ITER,
    allow_delegation=False,
    verbose=True,
)


auditor_agent = Agent(
    role="Safety Auditor",
    goal=(
        "Review the triage decision and resolution plan against hard safety "
        "rules, and reject anything that breaks them."
    ),
    backstory=(
        "When a case is ambiguous you assign a HIGHER urgency level, never a "
        "lower one: a routine case wrongly marked urgent costs a doctor twenty "
        "minutes, while an emergency wrongly marked routine can cost a life."
    ),
    tools=[],
    llm=llm,
    max_iter=MAX_ITER,
    allow_delegation=False,
    verbose=True,
)