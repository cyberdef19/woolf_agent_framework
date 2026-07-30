from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Literal
from pathlib import Path

class SpecificInput(BaseModel):
    """Загальний клас для параметрів входу інструментів"""
    config = ConfigDict(
        extra="forbid"
    )


class CalculateHashInput(SpecificInput):
    """Вхідні параметри для інструмента розрахунку хеша"""
    path_file: Path = Field(
        description="""
                    Шлях до файла, хеш якого слід розрахувати        
                    """)
    algorithm: Literal["md5", "sha1", "sha256"] = Field(
        default_factory="sha256",
        description="""
                     Алгоритм за яким відбувається хешування
                    """            
    ) 
    
    @field_validator("path_file", mode="before")
    @classmethod
    def validate_path_file(cls, value: Path) ->Path:
        """Валідує чи шлях до файлу передано в параметр"""
        
      
            
    