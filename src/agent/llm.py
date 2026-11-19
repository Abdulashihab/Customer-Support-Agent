import os
from pathlib import Path

from dotenv import load_dotenv

# Read the secret key from the .env file in the project folder.
# This file is src/agent/llm.py, so the project folder is 2 levels up.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

OPENROUTER_URL = "https://openrouter.ai/api/v1"


def _read_settings():
    """Read the key and the model name from the .env file."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL")
    if not api_key or not model:
        raise RuntimeError("Set OPENROUTER_API_KEY and OPENROUTER_MODEL in the .env file")
    return api_key, model


def get_llm():
    """LangChain style connection (we will use this later with LangGraph)."""
    from langchain_openai import ChatOpenAI

    api_key, model = _read_settings()
    return ChatOpenAI(model=model, api_key=api_key, base_url=OPENROUTER_URL, temperature=0)


def get_client():
    """Plain OpenAI style connection (used by the agent loop)."""
    from openai import OpenAI

    api_key, _ = _read_settings()
    return OpenAI(api_key=api_key, base_url=OPENROUTER_URL)


def get_model_name():
    """The model name chosen in the .env file."""
    return _read_settings()[1]