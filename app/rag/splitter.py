from langchain_text_splitters import RecursiveCharacterTextSplitter

def get_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

def split_docs(docs):
    splitter = get_text_splitter()
    return splitter.split_documents(docs)