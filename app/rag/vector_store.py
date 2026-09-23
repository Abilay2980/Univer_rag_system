from functools import lru_cache
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models
from app.rag.embeddings import get_embeddings

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "kaznu"

@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL)

def get_vectorstore() -> QdrantVectorStore:
    return QdrantVectorStore(
        client=get_qdrant_client(),
        collection_name=COLLECTION_NAME,
        embedding=get_embeddings(),
    )

def create_vectorstore(splits) -> QdrantVectorStore:
    return QdrantVectorStore.from_documents(
        documents=splits,
        embedding=get_embeddings(),
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
        force_recreate=True,
    )

def add_documents_to_vectorstore(splits):
    vectorstore = get_vectorstore()
    vectorstore.add_documents(documents=splits)

def delete_documents_by_ids(ids: list[str]):
    """Удаление чанков по ID."""
    vectorstore = get_vectorstore()
    vectorstore.delete(ids=ids)

def delete_documents_by_source(source_url: str):
    """Удаление всех чанков новости по URL статьи."""
    client = get_qdrant_client()
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.source",
                        match=models.MatchValue(value=source_url),
                    )
                ]
            )
        )
    )

def update_document_by_source(source_url: str, new_splits):
    """Обновление статьи: удаление старых чанков и запись новых."""
    delete_documents_by_source(source_url)
    add_documents_to_vectorstore(new_splits)

def get_retriever():
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 5,
            "fetch_k": 20,
            "lambda_mult": 0.7
        }
    )