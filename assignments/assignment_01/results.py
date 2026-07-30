from src.woolf_agents.core.result import BaseExecutionResult
from pydantic import BaseModel, ConfigDict

class SpecificResult(BaseModel):
    """Загальний клас для конкретних результатів"""
    config = ConfigDict(
            extra="forbid"
        )    

class MetadataFile(SpecificResult):
    """Отримує метадані файлу"""
    filename: str
    filepath: str
    filesize_bytes: int
    extension: str| None = None

class FileHash(SpecificResult):
    """Отримує хеш файлу"""
   
    algorithm: str
    value: str

class ExtractedStrings(SpecificResult):
    """Отримує рядки з файлу"""
    strings: list[str]
    total_count: int

class SuspiciousIndicators(SpecificResult):
    """Отримує список підозрілих індикаторів з файла"""

    indicators: list[str]
    total_count: int
    

class AssignmentResult01(BaseExecutionResult):
    """Основний результат після виконання усіх завдань"""
    metadata: MetadataFile
    filehash: FileHash
    extracted_strings: ExtractedStrings
    suspicious_artifacts: SuspiciousIndicators
    
    