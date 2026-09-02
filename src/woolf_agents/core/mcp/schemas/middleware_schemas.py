from pydantic import BaseModel


class RateLimittingArgs(BaseModel):
    max_requests_per_sec = 5.0
    burst_capacity = 10

class ErrorHandlingArgs(BaseModel):
    include_traceback = False
    transform_errors = True