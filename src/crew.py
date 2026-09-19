import time
from crewai import Crew, Process
from src.tasks import build_tasks
from src.agents import (
    intake_agent, triage_agent, resolver_agent, auditor_agent
)


def run_triage(raw_message: str, pause: int = 20):
    tasks = build_tasks(raw_message)

    for t in tasks:
        t.callback = lambda _out, p=pause: time.sleep(p)

    crew = Crew(
        agents=[intake_agent, triage_agent, resolver_agent, auditor_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    return result, tasks