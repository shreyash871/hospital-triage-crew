import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

MAX_ITER = int(os.getenv("MAX_ITER", 3))


def get_llm(temperature: float = 0.1) -> LLM:
    model = os.getenv("MODEL_NAME", "")
    key = (
        os.getenv("GEMINI_API_KEY")
        if model.startswith("gemini/")
        else os.getenv("GROQ_API_KEY")
    )
    return LLM(
        model=model,
        api_key=key,
        temperature=temperature,
        max_tokens=1000,
    )