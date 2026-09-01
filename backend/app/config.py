from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LLM_PROVIDER: str = "gemini"
    OPENAI_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    GENERATION_MODEL: str = "gemini-2.0-flash"
    EMBEDDING_DIMENSION: int = 3072

    POSTGRES_USER: str = "raguser"
    POSTGRES_PASSWORD: str = "ragpass"
    POSTGRES_DB: str = "ragdb"
    POSTGRES_HOST: str = "sqlite"
    POSTGRES_PORT: int = 5432

    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 60
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.25

    API_PORT: int = 8000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def api_key(self) -> str | None:
        return self.GOOGLE_API_KEY or self.GEMINI_API_KEY or self.OPENAI_API_KEY

    @property
    def database_url(self) -> str:
        if self.POSTGRES_HOST == "sqlite":
            return "sqlite:///./app.db"
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
