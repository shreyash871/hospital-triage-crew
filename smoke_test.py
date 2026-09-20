import os
from dotenv import load_dotenv
from src.config import get_llm

load_dotenv()

llm = get_llm()

response = llm.call([
    {"role": "user", "content": "Reply with exactly: connection ok"}
])

print(response)