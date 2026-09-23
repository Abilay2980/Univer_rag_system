from app.rag.loader import load_documents
from app.rag.splitter import split_docs
from app.rag.vector_store import create_vectorstore

def run_ingestion():
    docs = load_documents()
    splits = split_docs(docs)
    create_vectorstore(splits)
    
    print("Индексация завершена успешно!")

if __name__ == "__main__":
    run_ingestion()