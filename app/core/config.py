from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Embeddings Service"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/v1"

    # Database settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/embeddings"

    # Ollama settings
    OLLAMA_URL: str = "http://localhost:11434"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=("config.env", "config.local.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
