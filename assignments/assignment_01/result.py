from src.woolf_agents.core.result import BaseExecutionResult 
from src.woolf_agents.domains.artifacts.schemas.contracts import (
    MetadataFileResult,
    FileHashResult,
    ExtractedStringsResult,
    SuspiciousIndicatorsResult
    )

class AssignmentResult01(BaseExecutionResult):
    """Основний результат після виконання усіх завдань"""
    metadata: MetadataFileResult
    filehash: FileHashResult
    extracted_strings: ExtractedStringsResult
    suspicious_artifacts: SuspiciousIndicatorsResult