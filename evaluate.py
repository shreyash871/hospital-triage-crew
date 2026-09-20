import json
import time
from pathlib import Path
from src.crew import run_triage

SAMPLES = json.loads(Path("data/sample_messages.json").read_text())

results = []

for i, sample in enumerate(SAMPLES):
    print(f"\n{'='*60}\nRunning {sample['id']}\n{'='*60}")
    start = time.time()

    try:
        metrics, tasks = run_triage(sample["text"], message_id=sample["id"])
        triage = tasks[1].output.pydantic
        resolution = tasks[2].output.pydantic
        audit = tasks[3].output.pydantic

        results.append({
            "id": sample["id"],
            "expected": sample["expected_urgency"],
            "actual": triage.urgency.value,
            "correct": triage.urgency.value == sample["expected_urgency"],
            "department": triage.department.value,
            "action": resolution.action.value,
            "human_review": triage.requires_human_review,
            "audit_approved": audit.approved,
            "violations": audit.violations,
            "seconds": round(time.time() - start, 1),
            "total_tokens": metrics["total_tokens"],
            "total_llm_calls": metrics["total_llm_calls"],
        })
    except Exception as e:
        results.append({
            "id": sample["id"],
            "expected": sample["expected_urgency"],
            "actual": "RUN_FAILED",
            "correct": False,
            "error": str(e)[:200],
            "seconds": round(time.time() - start, 1),
        })

    if i < len(SAMPLES) - 1:
        print("\ncooling down 20s...")
        time.sleep(20)

Path("outputs").mkdir(exist_ok=True)
Path("outputs/eval_results.json").write_text(json.dumps(results, indent=2))

print(f"\n\n{'='*60}\nSUMMARY\n{'='*60}")

correct = sum(1 for r in results if r["correct"])
print(f"Urgency accuracy: {correct}/{len(results)}")

missed_emergencies = [
    r for r in results
    if r["expected"] == "EMERGENCY" and r["actual"] != "EMERGENCY"
]
print(f"Missed emergencies: {len(missed_emergencies)}")

false_positives = [
    r for r in results
    if r.get("audit_approved") is False
]
print(f"Audit rejections: {len(false_positives)}")

token_runs = [r for r in results if "total_tokens" in r]
if token_runs:
    avg_tokens = sum(r["total_tokens"] for r in token_runs) / len(token_runs)
    avg_calls = sum(r["total_llm_calls"] for r in token_runs) / len(token_runs)
    print(f"Mean tokens per run: {avg_tokens:.0f}")
    print(f"Mean LLM calls per run: {avg_calls:.1f}")

print()
for r in results:
    mark = "PASS" if r["correct"] else "FAIL"
    tok = r.get("total_tokens", "-")
    print(f"{r['id']} {mark}  expected={r['expected']:<9} "
          f"actual={r['actual']:<12} {r.get('seconds')}s  {tok} tok")