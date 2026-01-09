import os
from dotenv import load_dotenv

load_dotenv()

ENGINE = os.getenv("ENGINE", "OPENAI").upper()


def create_client_from_env():
    if ENGINE == "GEMINI":
        from .gemini_client import GeminiLLMClient
        return GeminiLLMClient.from_environment()
    elif ENGINE == "OPENAI":
        from .openai_client import OpenAIClient
        return OpenAIClient.from_environment()
    elif ENGINE == "ANTHROPIC":
        from .anthropic_client import AnthropicClient
        return AnthropicClient.from_environment()
    elif ENGINE == "LLAMA_CPP":
        from .llama_client import LlamaClient
        return LlamaClient.from_environment()
    else:
        raise RuntimeError(f"Unknown ENGINE: {ENGINE}")


def get_engine_name() -> str:
    return ENGINE
