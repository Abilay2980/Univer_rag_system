from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from langsmith import traceable

from app.core.config import settings
from app.rag.vector_store import get_retriever


def format_docs(docs, max_chars: int = 8000) -> str:
    formatted = []
    total_len = 0

    for doc in docs:
        source = doc.metadata.get("source", "unknown_source")
        page = doc.metadata.get("page", None)

        header = f"Source: {source}"
        if page is not None:
            header += f" | Page: {page}"

        text = doc.page_content.strip()
        block = f"{header}\n{text}"

        if total_len + len(block) > max_chars:
            break

        formatted.append(block)
        total_len += len(block)

    return "\n\n---\n\n".join(formatted)


prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Ты помощник, который отвечает СТРОГО НА РУССКОМ ЯЗЫКЕ. "
        "Используй только информацию из предоставленного контекста, не придумывай факты. "
        "Если ответа в контексте нет или данных недостаточно, честно скажи, что не нашёл ответа в базе. "
        "При необходимости можешь упоминать источник в формате из заголовка (Source и Page). "
        "Отвечай кратко и по делу, обычно до 5–7 предложений.",
    ),
    MessagesPlaceholder("history"),
    ("human", "Контекст:\n{context}\n\nВопрос: {question}"),
])


llm = ChatOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    model=settings.LLM_MODEL,
    temperature=0.2,
    max_tokens=512,
    top_p=0.9,
)


def ensure_context(input_dict: dict) -> dict:
    context = input_dict.get("context", "").strip()
    if not context:
        input_dict["context"] = (
            "Контекст пуст: ретривер не нашёл ни одного подходящего фрагмента. "
            "Если ответ важен, лучше явно сказать пользователю об этом."
        )
    return input_dict


rag_chain = (
    {
        "context": lambda d: d.get("context", ""),
        "question": lambda d: d.get("question", ""),
        "history": lambda d: d.get("history", []),
    }
    | RunnableLambda(ensure_context)
    | prompt
    | llm
    | StrOutputParser()
).with_config(run_name="rag_chain")


@traceable(name="AW_answer_question")
async def answer_question(question: str, context: str, history: list = None) -> str:
    inputs = {
        "question": question,
        "context": context,
        "history": history or [],
    }
    # Асинхронный генератор ответа
    return await rag_chain.ainvoke(inputs)


async def ask_rag(question: str, history: list = None) -> str:
    retriever = get_retriever()
    
    # Асинхронный поиск векторов в Qdrant
    docs = await retriever.ainvoke(question)
    ctx = format_docs(docs)
    
    return await answer_question(question=question, context=ctx, history=history)