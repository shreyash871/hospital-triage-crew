import json
import time
from crewai import Crew, Process
from src.tasks import build_intake_tasks, build_resolution_tasks
from src.agents import (
    intake_agent, triage_agent, resolver_agent, auditor_agent
)
from src.tools.schedule_tools import GetDoctorScheduleTool
from src.tools.capacity_tools import CheckBedAvailabilityTool
from src.observability.tracker import RunTracker

schedule_tool = GetDoctorScheduleTool()
bed_tool = CheckBedAvailabilityTool()


def run_triage(raw_message: str, pause: int = 13, message_id: str = "adhoc"):
    tracker = RunTracker(message_id)

    # Stage 1 — parse and classify
    stage1 = build_intake_tasks(raw_message)
    for t in stage1:
        t.callback = lambda _out, p=pause: time.sleep(p)

    crew1 = Crew(
        agents=[intake_agent, triage_agent],
        tasks=stage1,
        process=Process.sequential,
        verbose=True,
    )
    t0 = time.time()
    out1 = crew1.kickoff()
    tracker.record("intake_triage", out1, time.time() - t0)

    triage = stage1[1].output.pydantic
    department = triage.department.value

    # Deterministic data fetch — no LLM involved
    availability = schedule_tool._run(department)
    beds = bed_tool._run(department)

    # Stage 2 — resolve and audit
    stage2 = build_resolution_tasks(
        raw_message=raw_message,
        intake=stage1[0].output.pydantic,
        triage=triage,
        availability=availability,
        beds=beds,
    )
    for t in stage2:
        t.callback = lambda _out, p=pause: time.sleep(p)

    crew2 = Crew(
        agents=[resolver_agent, auditor_agent],
        tasks=stage2,
        process=Process.sequential,
        verbose=True,
    )
    t1 = time.time()
    out2 = crew2.kickoff()
    tracker.record("resolve_audit", out2, time.time() - t1)

    metrics = tracker.save()
    return metrics, stage1 + stage2