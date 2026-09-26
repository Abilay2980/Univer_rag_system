from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=find_dotenv())

    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    SECRET_WORD:str
    CACHE_URL:str
    BASE_URL:str
    LLM_MODEL:str
    EMBEDDING_MODEL:str
    API_KEY:str
    UNIVER_LOGIN:str
    UNIVER_PASSWORD:str
    QDRANT_REST_PORT:str
    QDRANT_GRPC_PORT:str
    OLLAMA_API_KEY:str
    OLLAMA_BASE_URL:str
    LANGSMITH_TRACING: bool = True
    LANGSMITH_ENDPOINT: str 
    LANGSMITH_API_KEY: str 
    LANGSMITH_PROJECT: str 
    


    @property
    def ASYNC_DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
