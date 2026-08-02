from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from .apikey import config



class LLMProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE_GENAI = "google_genai"
    OLLAMA = "ollama"

class LLMModel(StrEnum):
    GEMINI25FLASH = "gemini-2.5-flash"

class LLMSettings(BaseSettings):
    """Configuration used to initialize a chat language model."""

    model_config = SettingsConfigDict(
        extra="ignore",
    )

    provider: LLMProvider = Field(
        default_factory=LLMProvider.GOOGLE_GENAI,
        description="Provider used to initialize the chat model.",
    )

    model: str = Field(
        min_length=1,
        description="Provider-specific model identifier.",
    )
    
    api_key:str = Field(
        description="""
                    Ключ для api провайдера 
                    """
    )

    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature used for model generation.",
    )

    timeout_seconds: float = Field(
        default=60.0,
        gt=0,
        description="Maximum duration of a single model request.",
    )

    max_retries: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Maximum number of retries performed by the model client.",
    )