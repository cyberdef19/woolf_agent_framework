from pydantic import BaseModel, ConfigDict, Field, field_validator
from pathlib import Path

class SpecificResult(BaseModel):
    """Загальний клас для конкретних результатів"""
    model_config = ConfigDict(
            extra="forbid"
        )  
    filepath: Path      

class SpecificInput(BaseModel):
    """Загальний клас для параметрів входу інструментів"""
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        hide_input_in_errors=True
    )
    artifact_path: Path = Field(
            description="""
                        Шлях до файла      
                        """)
    @field_validator("artifact_path")
    @classmethod
    def validate_path_file(cls, value: Path) ->Path:
            """Валідує чи шлях до файлу передано в параметр"""
            if value is None:
                raise ValueError("Шлях до файла не може бути None")
            if not value.exists():
                raise ValueError("Такого шляху до файла не існує")
            if not value.is_file():
                raise ValueError("Має бути передано файл як аргумент")
            return value
            
