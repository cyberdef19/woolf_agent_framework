from pydantic import BaseModel, ConfigDict


class GuardResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    allowed: bool
    reason: str | None = None

class InputGuardResult(GuardResult):
    injection_detected: bool = False
