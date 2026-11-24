import json
import secrets

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] | str = ["http://localhost:5173", "http://127.0.0.1:5173"]

    DATABASE_URL: str = "sqlite:///./studyset.db"

    # Authentication
    SECRET_KEY: str = secrets.token_hex(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM Settings (Ollama - local primary)
    LLM_PRIMARY_PROVIDER: str = "ollama"   # ollama, gemini, groq
    LLM_FALLBACK_PROVIDER: str = "groq"    # groq, gemini, none

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:4b"
    OLLAMA_TIMEOUT_SECONDS: int = 180
    OLLAMA_NUM_CTX: int = 8192

    # LLM Settings (Google Gemini)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # LLM Settings (Groq Fast Inference / Fallback)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # Ingestion & Validation Limits
    MAX_INPUT_CHARACTERS: int = 50000
    MAX_UPLOAD_SIZE_MB: int = 15
    RESUME_UPLOAD_SIZE_MB: int = 10
    CHUNK_SIZE_TOKENS: int = 1000
    CHUNK_OVERLAP_TOKENS: int = 150
    REQUEST_TIMEOUT_SECONDS: int = 60
    MAX_REGENERATION_ATTEMPTS: int = 2

    # Upload storage
    UPLOAD_DIR: str = "./uploads"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @property
    def has_gemini_key(self) -> bool:
        return bool(
            self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip() and self.GEMINI_API_KEY != "your_gemini_api_key_here"
        )

    @property
    def has_groq_key(self) -> bool:
        return bool(
            self.GROQ_API_KEY and self.GROQ_API_KEY.strip() and self.GROQ_API_KEY != "your_groq_api_key_here"
        )

    @property
    def has_ollama(self) -> bool:
        """Check if Ollama is configured (doesn't verify connectivity)."""
        return bool(self.OLLAMA_BASE_URL and self.OLLAMA_MODEL)

    @property
    def has_any_llm_key(self) -> bool:
        return self.has_gemini_key or self.has_groq_key


settings = Settings()
