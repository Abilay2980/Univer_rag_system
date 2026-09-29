from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from langsmith import traceable

from app.core.config import settings
from app.rag.vector_store import get_retriever
from app.llm.client import llm_with_fallback 

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
        "Ты — официальный AI-помощник студентов (Univer / КазНУ).\n\n"
        "ПРАВИЛА ОТВЕТА:\n"
        "1. Отвечай СТРОГО НА РУССКОМ ЯЗЫКЕ.\n"
        "2. Используй ТОЛЬКО предоставленный ниже Контекст. Не придумывай факты, даты, имена и правила от себя.\n"
        "3. Если контекст пуст или в нем НЕТ прямого ответа на вопрос, ответь ровно одной фразой: "
        "«В базе данных Univer нет информации по вашему запросу.»\n"
        "4. Отвечай кратко, по существу, без лишней «воды» и эмоций.\n"
        "5. Если информация содержит списки или шаги — форматируй их структурировано.\n"
        "6. Приводи конкретные примеры из контекста, если они там присутствуют.\n\n"
        "Контекст:\n{context}"
    ),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])



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
    | llm_with_fallback
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
    
    docs = await retriever.ainvoke(question)
    ctx = format_docs(docs)
    
    return await answer_question(question=question, context=ctx, history=history)