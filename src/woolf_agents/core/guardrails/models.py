from pydantic import BaseModel

class GuardResult(BaseModel):
    allowed: bool
    reason: str | None = None

class InputGuardResult(GuardResult):
    injection_detected: bool = False

class InputGuard:
    ...

class OutputGuard:
    ...
    
class ToolGuard:
    ...