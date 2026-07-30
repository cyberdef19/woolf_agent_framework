from src.woolf_agents.core.result import BaseExecutionResult
from pydantic import BaseModel


class MetadataFile(BaseModel):
    """Отримує метадані файлу"""
    filename: str
    filepath: str
    filesize_bytes: int
    extension: str| None = None

class FileHash(BaseModel):
    """Отримує хеш файлу"""
    algorithm: str
    value: str

class ExtractedStrings(BaseModel):
    """Отримує рядки з файлу"""
    strings: list[str]
    total_count: int

class SuspiciousIndicators(BaseModel):
    """Отримує список підозрілих індикаторів з файла"""
    indicators: list[str]
    total_count: int
    

class AssignmentResult01(BaseExecutionResult):
    """Основний результат після виконання усіх завдань"""
    metadata: MetadataFile
    filehash: FileHash
    extracted_strings: ExtractedStrings
    suspicious_artifacts: SuspiciousIndicators
    
    