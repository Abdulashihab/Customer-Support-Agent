import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Read the secret key from the .env file in the project folder.
# This file is src/agent/llm.py, so the project folder is 2 levels up.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

OPENROUTER_URL = "https://openrouter.ai/api/v1"


def get_llm():
    """Create the AI model object. The key and the model name come from the .env file."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL")
    if not api_key or not model:
        raise RuntimeError("Set OPENROUTER_API_KEY and OPENROUTER_MODEL in the .env file")
    return ChatOpenAI(model=model, api_key=api_key, base_url=OPENROUTER_URL, temperature=0)