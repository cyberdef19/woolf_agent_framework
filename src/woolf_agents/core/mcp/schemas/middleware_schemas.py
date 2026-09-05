from pydantic import BaseModel


class RateLimittingArgs(BaseModel):
    max_requests_per_sec: float = 5.0
    burst_capacity: int = 10

class ErrorHandlingArgs(BaseModel):
    include_traceback: bool = False
    transform_errors: bool = True