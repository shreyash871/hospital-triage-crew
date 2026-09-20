import json
import time
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs"

# Process-wide running totals, since CrewAI reports cumulative usage
_seen = {"total": 0, "prompt": 0, "completion": 0, "calls": 0}


class RunTracker:
    """Records per-agent timing and token usage for one triage run."""

    def __init__(self, message_id: str = "adhoc"):
        self.message_id = message_id
        self.started = time.time()
        self.stages = []

    def record(self, stage_name: str, crew_output, elapsed: float):
        usage = getattr(crew_output, "token_usage", None)

        cum_total = getattr(usage, "total_tokens", 0)
        cum_prompt = getattr(usage, "prompt_tokens", 0)
        cum_completion = getattr(usage, "completion_tokens", 0)
        cum_calls = getattr(usage, "successful_requests", 0)

        # CrewAI reports cumulative usage per process, so subtract what
        # we have already counted to get this stage's real cost.
        stage = {
            "stage": stage_name,
            "seconds": round(elapsed, 1),
            "prompt_tokens": max(0, cum_prompt - _seen["prompt"]),
            "completion_tokens": max(0, cum_completion - _seen["completion"]),
            "total_tokens": max(0, cum_total - _seen["total"]),
            "llm_calls": max(0, cum_calls - _seen["calls"]),
        }

        _seen["total"] = max(_seen["total"], cum_total)
        _seen["prompt"] = max(_seen["prompt"], cum_prompt)
        _seen["completion"] = max(_seen["completion"], cum_completion)
        _seen["calls"] = max(_seen["calls"], cum_calls)

        self.stages.append(stage)

    def summary(self) -> dict:
        return {
            "message_id": self.message_id,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "total_seconds": round(time.time() - self.started, 1),
            "total_tokens": sum(s["total_tokens"] for s in self.stages),
            "total_llm_calls": sum(s["llm_calls"] for s in self.stages),
            "stages": self.stages,
        }

    def save(self):
        OUTPUT_DIR.mkdir(exist_ok=True)
        with open(OUTPUT_DIR / "run_metrics.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(self.summary()) + "\n")
        return self.summary()