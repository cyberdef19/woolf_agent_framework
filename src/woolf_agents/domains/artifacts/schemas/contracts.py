from typing import Self

from pydantic import Field, field_validator, model_validator, BaseModel
from .base import SpecificInput, SpecificResult, BaseTaskPlan, BasePlanStep, BaseStepResult
from enum import Enum
from datetime import datetime
from pathlib import Path



class HashAlgorithm(str, Enum):
    MD5 = "md5",
    SHA1 = "sha1",
    SHA256 = "sha256"

class CalculateHashInput(SpecificInput):
    """Вхідні параметри для інструмента розрахунку хеша"""
   
    algorithm: HashAlgorithm = Field(
        default=HashAlgorithm.SHA256,
        description="""
                     Алгоритм за яким відбувається хешування
                    """            
    ) 
    
    
    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, value: HashAlgorithm) -> str:
        """Валідує поле алгоритму algorithm"""
        if value is None:
            raise ValueError("Поле алгоритму не може бути пустим")
        if not isinstance(value, HashAlgorithm):
            raise TypeError("В поле алгоритму має передатися рядок")
        if not value in list(HashAlgorithm):
            raise ValueError("В полі алгоритму має бути дозволене значення зі списку")
        return value

class MetadataLevel(str, Enum):
    """Визначає рівень метаданих який слід отримати"""
    BASIC = "basic"
    EXTENDED = "extended"

class MetadataFileInput(SpecificInput):
    """Вхідні параметри для використання у інструменті отримання метаданних файлу"""
    metadata_level: MetadataLevel = Field(
        default=MetadataLevel.BASIC,
        description="""
                Рівень метаданих, який маємо отримати
        """    
    )
    
    @field_validator("metadata_level")
    @classmethod
    def validate_metadata_level(cls, value: MetadataLevel):
        """Валідує поле рівня метаданих metadata_level"""
        if not isinstance(value, MetadataLevel):
            raise TypeError("Поле має бути типу MetadataLevel")
        allow_levels = [item.value for item in MetadataLevel]
        if not value in allow_levels:
            raise ValueError("Недопустиме значення аргументу") 
        return value

class TextEncoding(str, Enum):
    """Перечислення для поля декодування encoding"""
    ASCII = "ascii"
    UTF8 = "utf-8"
    UTF16_LE = "utf-16-le"
    UTF16_BE = "utf-16-be"

class StringExtractMode(str, Enum):
    """Режим витягування рядків"""
    BOTH = "both"
    ASCII = "ascii"
    UNICODE = "unicode"

class ExtractStringsInput(SpecificInput):
    """Аргументи для екстракції рядків з файла"""
    encoding: TextEncoding = Field(
        default=TextEncoding.UTF8,
        description="""
                    Символи кодування, що мають використовуватися для кодування
                    рядків з байтових масивів. 
                    """
    )
    min_length: int = Field(
        default=4,
        ge=1,
        le=256,
        description="""
                    Мінімальна довжина з вилученого рядка 
                    """
    )
    max_length: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="""
                    Максимальна довжина вилученого рядка
                    """
    )
    max_strings: int = Field(
        default=1000,
        ge=1,
        le=100000,
        description="""
                    Максимальна кількість рядків, що може бути вилучена з файла
                    """ 
    )
    
    
    @field_validator("encoding")
    @classmethod
    def validate_encoding(cls, value: TextEncoding):
        """ Валідація значення в encoding"""
        if not isinstance(value, TextEncoding):
           raise TypeError("Поле має бути типу TextEncoding")
        allow_encoding = [item.value for item in TextEncoding]
        if not value in allow_encoding:
            raise ValueError("Недопустиме значення аргументу")
        return value
    


class TypeIndicators(str, Enum):
    """Типи підозрілих індикаторів """
    IPV4 = "ipv4"
    URL = "url"
    DOMAIN = "domain"
    EMAIL = "email"
    KEYWORD = "keyword"

class TypeSuspiciousKeywords(str, Enum):
    """Типи підозрілих ключових слів"""
    PASSWORD = "password"
    TOKEN = "token"
    SECRET = "secret"
    ADMIN = "admin"
    LOGIN = "login"
    APIKEY = "api_key"
    

class SuspiciousIndicatorsInput(SpecificInput):
    """Визначає вхідні аргументи для інструмента виявлення підозрілих індикаторів"""
    
    indicators_type: list[TypeIndicators] = Field(
        default_factory=lambda:list(TypeIndicators),
        description="""
                    Виявлення підозрілих індикаторів 
                    """
    )
    suspicious_keywords: list[TypeSuspiciousKeywords] = Field(
        default_factory=lambda:list(TypeSuspiciousKeywords),
        description="""
                    Виявлення підозрілих ключових слів
                    """
        
    )
    max_results: int = Field(
        default=500,
        ge=1,
        le=10_000,
        description="""
                    Максимальна кількість знайдених індикаторів, які має повернути інструмент 
                    """
        
    )
    
    @field_validator("indicators_type")
    @classmethod
    def validate_indicators(cls, value: list[TypeIndicators]):
        """Валідація типів індикаторів у полі indicators_type"""
        if not isinstance(value, list[TypeIndicators]):
            raise TypeError("Значенням аргументу у полі indicators_type має бути значення типу list[TypeIndicators]")
        allow_values = [item.value for item in TypeIndicators]
        exist_values = [item.value for item in value]
        if not all(item in allow_values for item in exist_values):
            raise ValueError("Наявні елементи, що не дозволені у переліку типів індикаторів")
        return value
    
    @field_validator("suspicious_keywords")
    @classmethod
    def validate_keywords_before(cls, value: TypeSuspiciousKeywords):
        """Валідація ключових слів перпеданих у поле suspicious_keywords"""
        if not isinstance(value, list[TypeSuspiciousKeywords]):
            raise TypeError("Невірний тип у полі suspicious_keywords")
        allow_values = [item.value for item in TypeSuspiciousKeywords]
        exist_values = [item.value for item in value]
        if not all(item in allow_values for item in exist_values):
            raise ValueError("Наявні елементи, що не дозволені у переліку типів ключових слів")
        return value
    
    @model_validator(mode="after")
    def validate_keyword_configuration(self) -> "SuspiciousIndicatorsInput": 
        """Валідація конфігурації ключових слів"""
        if (
            TypeIndicators.KEYWORD in self.indicators_type
            and not self.suspicious_keywords
            ):
            raise ValueError(
                      """
                      Якщо в поле типів підозрілих індикаторів передано тип KEYWORD,
                      то список ключових слів не може бути пустим в аргументі suspicious_keywords
                      """
            )
        return self

class MetadataFileResult(SpecificResult):
    """Отримує метадані файлу"""
    filename: str
    filepath: Path
    filesize_bytes: int
    extension: str| None = None
    created_at: datetime
    modified_at: datetime
    mimetype: str

class FileHashResult(SpecificResult):
    """Отримує хеш файлу"""
   
    algorithm: HashAlgorithm
    value: str
    processed_bytes: int

class ExtractedStringsResult(SpecificResult):
    """Отримує рядки з файлу"""
    strings: list[str]


class SuspiciousIndicatorsResult(SpecificResult):
    """Отримує список підозрілих індикаторів з файла"""
    indicators: list[str]
    total_count: int

#!---------------------------------------Контракти для агента планувальника--------------------------------


class HistoricalResearchStepResult(BaseStepResult):
    """Конкретизуючий результат кроку виконання плану"""
    


class HistoricalResearchStepPlan(BasePlanStep):
    """Крок для дослідницького плану історичний домен"""
    research_query: str| None = Field(
        default=None,
        description=(
            "Пошуковий запит до векторної бази. "
            "Заповнюй лише для operation='retrieve_sources'. "
            "Для інших operations залишай null."
        )
    )
    requires_evidence:bool = Field(
        description="Необхідність опиратися на історичні джерела"
    )
    @model_validator(mode="after")
    def validate_research_query(self) -> Self:

        if self.operation == "retrieve_sources":
            if not self.research_query:
                raise ValueError(
                    "research_query вимагаэться лише "
                    "для operation='retrieve_sources'"
                )

        elif self.research_query is not None:
            raise ValueError(
                "research_query повинно бути null "
                "коли operation не 'retrieve_sources'"
            )

        return self
    

class HistoricalResearchPlan(BaseTaskPlan):
    """Історичний дослідницький план під конкретний домен знань"""
    research_question: str = Field(
        description="Дослідницьке історичне питання, яке має бути вибудувано у план "
    )
    steps:list[HistoricalResearchStepPlan] = Field(
        description="Список кроків історичного дослідницького плану "
    )
    
class StepExecutionContext(BaseModel):
    user_task: str
    current_step: BasePlanStep
    previous_results: list[BaseStepResult]


