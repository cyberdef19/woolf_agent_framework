from pydantic import BaseModel, ConfigDict, Field, field_validator
from pathlib import Path

class SpecificResult(BaseModel):
    """Загальний клас для конкретних результатів"""
    config = ConfigDict(
            extra="forbid"
        )  
    filepath: Path      

class SpecificInput(BaseModel):
    """Загальний клас для параметрів входу інструментів"""
    config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        hide_input_in_errors=True
    )
    path_file: Path = Field(
            description="""
                        Шлях до файла, хеш якого слід розрахувати        
                        """)
    @field_validator("path_file", mode="before")
    @classmethod
    def validate_path_file(cls, value: Path) ->Path:
            """Валідує чи шлях до файлу передано в параметр"""
            if value is None:
                raise ValueError("Шлях до файла не може бути None")
            if not isinstance(value, Path):
                raise TypeError("Шлях має бути об'єктом типу Path")
            if not value.exists():
                raise ValueError("Такого шляху до файла не існує")
            if not value.is_file():
                raise ValueError("Має бути передано файл як аргумент")
