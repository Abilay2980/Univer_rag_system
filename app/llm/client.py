from openai import AsyncOpenAI
from app.core.config import settings
from fastapi import HTTPException, status
from langchain_openai import ChatOpenAI
from langchain_openai import ChatOpenAI
from app.core.config import settings

primary_llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.LLM_MODEL,
    request_timeout=10.0,
    max_tokens=1024
)

fallback_llm = ChatOpenAI(
    api_key=settings.OLLAMA_API_KEY,
    base_url=settings.OLLAMA_BASE_URL,
    model="gemma3:4b",
    request_timeout=30.0,
    max_tokens=1024
)

llm_with_fallback = primary_llm.with_fallbacks([fallback_llm])


async def ask_llm(q: str) -> str:
    response = await llm_with_fallback.ainvoke(q)
    return response.content