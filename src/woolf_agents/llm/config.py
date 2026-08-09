from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from .apikey import config
from .settings import url_modelrouter

class ConfigGoogleAPI(StrEnum):
    GOOGLEGEMINI = config.get("GEMINIAPYKEY", None)

class ConfigModelAPI(StrEnum):
    OPENROUTERKEY = config.get("OPENROUTERKEY", None)
    URLOPENROUTER = url_modelrouter.get("openrouter_url", None)
    GOOGLEGEMINI = config.get("GEMINIAPYKEY", None)

class LLMProvider(StrEnum):
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE_GENAI = "google_genai"
    OLLAMA = "ollama"

class LLMModel(StrEnum):
    GEMINI25FLASH = "gemini-2.0-flash"
    GOOGLEGEMMA426BA4BFREE = "google/gemma-4-26b-a4b-it:free"
    GOOGLEGEMMA431BFREE = "google/gemma-4-31b-it:free"
    LING30FLASHFREE = "inclusionai/ling-3.0-flash:free"
    GPTOSS20bFREE = "openai/gpt-oss-20b:free"
    LAGUNAS21FREE = "poolside/laguna-s-2.1:free"  #для завдань tool calling coding
    LAGUNAXS21FREE = "poolside/laguna-xs-2.1:free"  #для завдань tool calling coding
    S21PROFREE = "poolside/s2.1-pro:free"
    NEMOTRON3SUPERFREE = "nvidia/nemotron-3-super-120b-a12b:free"
    NEMOTRONNANO9BV2FREE = "nvidia/nemotron-nano-9b-v2:free"
    NEMOTRONNANO12B2VLFREE = "nvidia/nemotron-nano-12b-2vl:free"
    NEMOTRON3NANO30BA3bFREE = "nvidia/nemotron-3-nano-30b-a3b:free"
    NEMOTRON3ULTRAFREE = "nvidia/nemotron-3-ultra-550b-a55b:free"    #потужна модель, максимум розумових можливостей, на вершину fallback
    NEMOTRON3NANOOMNIFREE = "nvidia/nemotron-3-nano-omni:free"
    NEMOTRON3EMBED1BFREE = "nvidia/nemotron-3-embed-1b:free"         #векторні представлення
    NEMOTRON35CONTENTSAFETYFREE = "nvidia/nemotron-3.5-content-safety:free"   #безпека, фільтрація запитів
    IBMGRANITE418B = "ibm/granite-4.1-8b-instruct"     #0.05$M input tokens 0.10$M output tokens tool calling code generation RAG
    DEEPSEEKV4FLASH0731 = "deepseek/deepseek-v4-flash-0731" #0.083/0.167 by 1M tokens reasoning
    

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
    
    base_url:str = Field(
        default=None,
        description=" Базовий url провайдера"
    )

    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Sampling temperature used for model generation.",
    )

    llm_timeout_seconds: float = Field(
        default=240.0,
        gt=0,
        description="Maximum duration of an single model request.",
    )

    max_retries: int = Field(
        default=2,
        ge=0,
        le=10,
        description="Maximum number of retries performed by the model client.",
    )