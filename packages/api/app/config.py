from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://blueprint:blueprint@localhost:5432/blueprint"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    user_agent: str = "blueprint-transparencia/0.1"
    dir3_url: str = ""
    eurlex_proxy: str = ""
    # Fase 4 — LLM opcional para EXTRAER el sujeto de frases difíciles
    # (compatible OpenAI: OpenAI, Groq, Ollama, vLLM…). Sin clave, el motor
    # funciona 100% determinista. El veredicto lo decide la regla, nunca el LLM.
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""


@lru_cache
def settings() -> Settings:
    return Settings()
