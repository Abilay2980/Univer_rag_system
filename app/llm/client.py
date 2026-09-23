from openai import AsyncOpenAI
from app.core.config import settings
client = AsyncOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL

)
async def ask_llm(q:str):
    response = await client.chat.completions.create(
            model = settings.LLM_MODEL,
            messages=[{"role": "user", "content": q}]
            )
    return response.choices[0].message.content