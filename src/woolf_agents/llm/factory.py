from langchain_google_genai import ChatGoogleGenerativeAI
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
                    timeout=settings.timeout_seconds,
                    max_retries=settings.max_retries,
                )
            case _:
                raise ValueError("Непідтримуваний провайдер")
            