from fastapi import APIRouter, HTTPException
from openai import OpenAIError

from ..models.chat import ChatRequest, ChatResponse
from ..services.chat_service import get_chat_reply

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        reply = get_chat_reply(request.message)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except OpenAIError as exc:
        raise HTTPException(
            status_code=502, detail="Failed to get a response from the AI service."
        ) from exc
    return ChatResponse(reply=reply)
