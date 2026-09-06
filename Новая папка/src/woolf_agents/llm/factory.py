from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from .config import LLMSettings, LLMProvider



class LLMFactory:
    """Create chat models from validated platform configuration."""

    @staticmethod
    def create(settings: LLMSettings) -> BaseChatModel:
        match settings.provider:
            case LLMProvider.GOOGLE_GENAI:
                return ChatGoogleGenerativeAI(
                    model=settings.model,
                    temperature=settings.temperature,
                    google_api_key = settings.api_key,
                    timeout=settings.llm_timeout_seconds,
                    max_retries=settings.max_retries,
                )
            case LLMProvider.OPENROUTER:
                return ChatOpenAI(
                    model=settings.model,
                    base_url=settings.base_url,
                    api_key=settings.api_key,
                    temperature=settings.temperature,
                    max_retries=settings.max_retries,
                    timeout=settings.llm_timeout_seconds
                )
            case _:
                raise ValueError("Непідтримуваний провайдер")
            