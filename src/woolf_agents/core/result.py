from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict
from .errors import ErrorInfo

class ExecutionStatus(StrEnum):
    """Final status of an agent or workflow execution."""
    SUCCESS = "success"
    STOP="stopped"
    PARTIAL = "partial"
    FAILED = "failed"
    INTERRUPT = "interrupted"


class BaseExecutionResult(BaseModel):
    """
    Base model for the final result of an agent or workflow execution.

    Concrete agent systems should inherit from this model and add explicit
    domain-specific fields, such as an answer, sources, generated files,
    processed records, forensic findings, or artifacts.

    This model describes the public result returned after execution. It must
    not be used as a replacement for an internal workflow state, such as a
    LangGraph state object.
    """
    model_config = ConfigDict(
        extra="ignore",
        )
    
    status: ExecutionStatus = Field(
        description="""
            Final execution status. Use 'success' when the task produced the
            expected usable result, 'partial' when a usable result was produced
            but some operations failed or remained incomplete, and 'failed' 
            when no usable result could be produced.
            """
        )
    errors: list[str] = Field(
        default_factory=list,
        description=""" 
        Human-readable error messages collected during execution. 
        Leave the list empty when no errors occurred. A partial result 
        may contain errors while still providing useful output.
        """
    )
   
    summary: str = Field(
        description="""Узагальнюючий фінальний підсумок результата"""
    )