from functools import lru_cache
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from app.core.config import settings 

class PrefixedEmbeddings(Embeddings):
    def __init__(self, base: Embeddings, query_prefix: str = "query: ", doc_prefix: str = "passage: "):
        self.base = base
        self.query_prefix = query_prefix
        self.doc_prefix = doc_prefix

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.base.embed_documents([f"{self.doc_prefix}{t}" for t in texts])

    def embed_query(self, text: str) -> list[float]:
        return self.base.embed_query(f"{self.query_prefix}{text}")

@lru_cache(maxsize=1)
def get_embeddings() -> PrefixedEmbeddings:
    base = HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL,
    )
    return PrefixedEmbeddings(
        base=base,
        query_prefix="query: ",
        doc_prefix="passage: "
    )