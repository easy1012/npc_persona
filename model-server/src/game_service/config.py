from __future__ import annotations

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_dsn: SecretStr
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: SecretStr
    vllm_url: str
    model_name: str
    embedding_url: str = "http://vllm:8000/v1/embeddings"
    embedding_model: str = "google/gemma-4-E4B-it"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
