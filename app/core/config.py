from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Embeddings Service"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/v1"

    # Database settings
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/embeddings"

    model_config = {"case_sensitive": True, "env_file": "config.env"}


settings = Settings()
