import json
from src.crew import run_triage

MESSAGE = (
    "my father has chest pain since morning and his left arm feels numb, "
    "can we come today"
)

if __name__ == "__main__":
    result, tasks = run_triage(MESSAGE)

    print("\n" + "=" * 60)
    print("FINAL OUTPUTS")
    print("=" * 60)

    for t in tasks:
        print(f"\n--- {t.agent.role} ---")
        if t.output and t.output.pydantic:
            print(json.dumps(t.output.pydantic.model_dump(), indent=2))
        else:
            print(t.output.raw if t.output else "no output")