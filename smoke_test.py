import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()

llm = LLM(
    model=os.getenv("MODEL_NAME"),
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.1,
)

response = llm.call([
    {"role": "user", "content": "Reply with exactly: connection ok"}
])

print(response)