import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.crew import run_triage
from src.schemas import ParsedIntake, TriageDecision, ResolutionPlan, AuditResult

app = FastAPI(
    title="Hospital Ops Triage Crew",
    description=(
        "Multi-agent triage for unstructured patient messages. "
        "Operational routing only — not a clinical decision system."
    ),
    version="1.0.0",
)


class TriageRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Raw patient message as received by the ops desk",
        examples=["my father has chest pain since morning, can we come today"],
    )


class TriageResponse(BaseModel):
    intake: ParsedIntake
    triage: TriageDecision
    resolution: ResolutionPlan
    audit: AuditResult
    metrics: dict


@app.get("/health")
def health():
    """Liveness probe. Reports config without exposing secrets."""
    return {
        "status": "ok",
        "model": os.getenv("MODEL_NAME", "not configured"),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


@app.post("/triage", response_model=TriageResponse)
def triage(request: TriageRequest):
    """Run the 4-agent triage pipeline on one patient message."""
    try:
        metrics, tasks = run_triage(request.message)
    except Exception as e:
        # A triage system that cannot reach its model must fail loudly,
        # never return a default classification.
        raise HTTPException(
            status_code=503,
            detail=f"Triage pipeline unavailable: {type(e).__name__}",
        )

    outputs = [t.output.pydantic if t.output else None for t in tasks]

    if any(o is None for o in outputs):
        raise HTTPException(
            status_code=502,
            detail="Pipeline produced incomplete output; escalate to a human.",
        )

    return TriageResponse(
        intake=outputs[0],
        triage=outputs[1],
        resolution=outputs[2],
        audit=outputs[3],
        metrics=metrics,
    )
    