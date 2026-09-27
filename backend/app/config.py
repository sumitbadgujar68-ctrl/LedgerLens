from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    alchemy_api_key: Optional[str] = None
    alchemy_network: str = "eth-mainnet"
    llm_provider: str = "openai"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.1
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "google/gemma-4-26b-a4b-it:free"
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    enable_docs: bool = False
    sql_echo: bool = False

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def llm_provider_active(self) -> str:
        """Provider actually in use.

        ``LLM_PROVIDER`` selects it, falling back to whichever provider has a
        key configured so that setting only one provider's variables is enough.
        """
        configured = "openrouter" if self.openrouter_api_key else "openai"
        if self.openrouter_api_key and self.openai_api_key:
            configured = "openrouter" if self.llm_provider == "openrouter" else "openai"
        return configured

    @property
    def llm_api_key(self) -> Optional[str]:
        if self.llm_provider_active == "openrouter":
            return self.openrouter_api_key
        return self.openai_api_key

    @property
    def llm_base_url(self) -> Optional[str]:
        if self.llm_provider_active == "openrouter":
            return self.openrouter_base_url
        return None

    @property
    def llm_model(self) -> str:
        if self.llm_provider_active == "openrouter":
            return self.openrouter_model
        return self.openai_model


    class Config:
        env_file = ".env"

settings = Settings()
