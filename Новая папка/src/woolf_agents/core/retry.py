from pydantic import BaseModel, Field, ConfigDict
from tenacity import (
    AsyncRetrying,
    wait_random_exponential,
    stop_after_attempt,
    retry_if_exception,
    retry_if_exception_type,
    before_sleep_log
    )
import logging
import httpx

logger = logging.getLogger(__name__)


class RetrySettings(BaseModel):
    """
    Configuration controlling repeated execution after transient failures.
    """
    model_config=ConfigDict(
        extra="forbid"
    )
    max_attempts: int = Field(
        default=3,
        ge=1,
        description=(
            "Maximum total number of execution attempts, including the initial "
            "attempt."
        ),
    )

    initial_delay_seconds: float = Field(
        default=1.0,
        ge=0,
        description=(
            "Delay before the first retry attempt."
        ),
    )

    backoff_multiplier: float = Field(
        default=2.0,
        ge=1,
        description=(
            "Multiplier applied to the delay after each failed attempt."
        ),
    )

    max_delay_seconds: float = Field(
        default=30.0,
        ge=0,
        description=(
            "Maximum delay allowed between retry attempts."
        ),
    )
    
class RetryPolicyAgent:
    
    def __init__(self, settings: RetrySettings):
        self._settings = settings
    
    def is_retryable_http_status(self, exc: BaseException) -> bool:
        return (
            isinstance(exc, httpx.HTTPStatusError)
            and exc.response.status_code
            in {429, 502, 503, 504}
        )
    
    def create_retrying(self)->AsyncRetrying:
        print(type(self._settings))
        return AsyncRetrying(
            stop=stop_after_attempt(
                self._settings.max_attempts
            ),
            wait=wait_random_exponential(
                multiplier=self._settings.backoff_multiplier,
                min=self._settings.initial_delay_seconds,
                max=self._settings.max_delay_seconds
            ),
            retry= (
                    retry_if_exception_type(
                        (
                            httpx.TimeoutException,
                            httpx.ConnectError,
                            httpx.NetworkError,
                        )
                        )
                        |
                    retry_if_exception(
                            self.is_retryable_http_status
                        )
                ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True
            
        )
        
    