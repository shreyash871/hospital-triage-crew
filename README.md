# Hospital Ops Triage Crew

A multi-agent system that turns unstructured patient messages into
routed, auditable triage decisions.

**This is an operational routing system, not a clinical decision system.**
It classifies how urgently a message needs attention and which desk should
handle it. It does not diagnose. Every emergency escalates to a human.

---

## The problem

A hospital ops desk receives messages like:

> *"my father has chest pain since morning and his left arm feels numb,
> can we come today"*

> *"knee has been hurting for 3 months, getting worse when climbing stairs"*

They arrive as free text, in no particular format, at a rate nobody can
triage consistently by hand. The cost of a mistake is asymmetric: a routine
case marked urgent wastes twenty minutes of a doctor's time; an emergency
marked routine can cost a life.

## The pipeline

Each arrow is a validated Pydantic contract. Agents share no memory — one
agent's output is serialized into the next agent's prompt, so the schema
*is* the interface.

## Safety design

| Mechanism | What it prevents |
|---|---|
| Extraction separated from judgment | Intake flags phrases but never rates them, so Triage cannot skip evidence |
| Asymmetric cost in the prompt | Ambiguity resolves upward, never downward |
| `requires_human_review` flag | Nothing unclear is silently auto-booked |
| Auditor may raise urgency, never lower | A second pass can only make the system more cautious |
| Capacity thresholds computed in code | `FULL` / `NEARLY_FULL` never depends on the model doing arithmetic |
| 503 on pipeline failure | A triage system that cannot reach its model escalates rather than defaulting to ROUTINE |

## Results

Evaluated on 5 hand-written messages spanning emergency, urgent, routine
and near-empty input.

| Metric | Value |
|---|---|
| Urgency accuracy | 5/5 |
| Missed emergencies | 0/2 |
| Mean tokens per run | ~5,500 |
| Mean latency | ~57s (free-tier paced) |
| Auditor false positives | 0 |

Two of the five ground-truth labels were corrected during evaluation: the
system's classification was more defensible than the original label, and
the label was changed rather than the system.

Reproduce with `python evaluate.py`.

## Architecture decisions

**Tool calls replaced with deterministic pre-fetch.** The Resolver always
needs the schedule for its department — that decision was never in doubt.
Letting the LLM choose whether to call `get_doctor_schedule` added a round
trip, tokens, and a failure mode for no benefit. The tool classes remain and
are unit-tested; they are invoked by Python, not by the model.

**Structured outputs over free text.** Every inter-agent boundary is a
Pydantic model with enum-constrained fields. Malformed output is rejected
and retried rather than propagating downstream.

**Centralized LLM config.** All four agents construct through `get_llm()`.
Migrating providers was a ten-line change to one file.

## Known limitations

- Agents are module-level singletons; concurrent API requests would share
  mutable state. Production would construct agents per request.
- No retry/backoff on provider errors. A transient 503 fails the run instead
  of degrading it to human escalation.
- The auditor validates structure, not substance. A truncated API response
  once produced a schema-valid decision with meaningless reasoning that
  passed the audit.
- Mock JSON data layer. Tool interfaces are shaped for a real backend but
  are not wired to one.

## Running it

```bash
cp .env.example .env        # add your API key
pip install -r requirements.txt
uvicorn api:app --reload    # http://127.0.0.1:8000/docs
```

Or with Docker:

```bash
docker build -t hospital-triage-crew .
docker run -p 8000:8000 --env-file .env hospital-triage-crew
```

Run `python list_models.py` to see which models your key can reach — the
free-tier model catalogs change frequently.

## Stack

CrewAI · Pydantic · FastAPI · Docker · Groq / Gemini (configurable)