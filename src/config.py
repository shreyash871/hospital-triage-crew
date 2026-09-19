import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

MAX_ITER = int(os.getenv("MAX_ITER", 3))


def get_llm(temperature: float = 0.1) -> LLM:
    return LLM(
        model=os.getenv("MODEL_NAME"),
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=temperature,
        max_tokens=1000,
    )