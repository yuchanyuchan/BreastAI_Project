from openai import OpenAI

from ..core.config import OPENAI_API_KEY, OPENAI_MODEL

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def get_chat_reply(message: str) -> str:
    client = _get_client()
    response = client.responses.create(model=OPENAI_MODEL, input=message)
    return response.output_text
