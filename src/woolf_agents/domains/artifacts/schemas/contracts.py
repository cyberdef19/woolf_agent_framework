from pydantic import Field, field_validator, model_validator
from typing import Literal
from .base import SpecificInput, SpecificResult
from src.woolf_agents.core.result import BaseExecutionResult
from enum import Enum
from datetime import datetime


class HashAlgorithm(str, Enum):
    MD5 = "md5",
    SHA1 = "sha1",
    SHA256 = "sha256"

class CalculateHashInput(SpecificInput):
    """Вхідні параметри для інструмента розрахунку хеша"""
   
    algorithm: HashAlgorithm = Field(
        default_factory=HashAlgorithm.SHA256,
        description="""
                     Алгоритм за яким відбувається хешування
                    """            
    ) 
    
    
    @field_validator("algorithm", mode="before")
    @classmethod
    def validate_algorithm(cls, value: str) -> str:
        """Валідує поле алгоритму algorithm"""
        if value is None:
            raise ValueError("Поле алгоритму не може бути пустим")
        if not isinstance(value, str):
            raise TypeError("В поле алгоритму має передатися рядок")
        if not value in list(HashAlgorithm):
            raise ValueError("В полі алгоритму має бути дозволене значення зі списку")

class MetadataLevel(str, Enum):
    """Визначає рівень метаданих який слід отримати"""
    BASIC = "basic"
    EXTENDED = "extended"

class MetadataFileInput(SpecificInput):
    """Вхідні параметри для використання у інструменті отримання метаданних файлу"""
    metadata_level: MetadataLevel = Field(
        default_factory=MetadataLevel.BASIC,
        description="""
                Рівень метаданих, який маємо отримати
        """    
    )
    
    @field_validator("metadata_level", mode="before")
    @classmethod
    def validate_metadata_level(cls, value: MetadataLevel):
        """Валідує поле рівня метаданих metadata_level"""
        if not isinstance(value, MetadataLevel):
            raise TypeError("Поле має бути типу MetadataLevel")
        allow_levels = [item.value for item in MetadataLevel]
        if not value in allow_levels:
            raise ValueError("Недопустиме значення аргументу") 

class TextEncoding(str, Enum):
    """Перечислення для поля декодування encoding"""
    AUTO = "auto"
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
        default_factory=TextEncoding.AUTO,
        description="""
                    Символи кодування, що маю використовуватися для кодування
                    рядків з байтових масивів. Використовуйте "auto" для автоматичного
                    вибору символів кодування.
                    """
    )
    min_length: int = Field(
        default_factory=4,
        ge=1,
        le=256,
        description="""
                    Мінімальна довжина з вилученого рядка 
                    """
    )
    max_length: int = Field(
        default_factory=1000,
        ge=1,
        le=10000,
        description="""
                    Максимальна довжина вилученого рядка
                    """
    )
    max_strings: int = Field(
        default_factory=1000,
        ge=1,
        le=100000,
        description="""
                    Максимальна кількість рядків, що може бути вилучена з файла
                    """ 
    )
    
    """mode:StringExtractMode = Field(
        default_factory=StringExtractMode.BOTH,
        description=
                          
                    
        
    )"""
    
    @field_validator("encoding", mode="before")
    @classmethod
    def validate_encoding(cls, value: TextEncoding):
        """ Валідація значення в encoding"""
        if not isinstance(value, TextEncoding):
           raise TypeError("Поле має бути типу TextEncoding")
        allow_encoding = [item.value for item in TextEncoding]
        if not value in allow_encoding:
            raise ValueError("Недопустиме значення аргументу")
    
    """@field_validator("mode", mode="before")
    @classmethod
    def validate_mode(cls, value: StringExtractMode):
        "Валідація значення в полі mode"
        if not isinstance(value, StringExtractMode):
            raise TypeError("Аргумент має бути типом StringExtractMode")
        allow_modes = [item.value for item in StringExtractMode]
        if not value in allow_modes:
            raise ValueError("Недопустиме значення аргументу")
    """

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
    
    @field_validator("indicators_type", mode="before")
    @classmethod
    def validate_indicators(cls, value: list[TypeIndicators]):
        """Валідація типів індикаторів у полі indicators_type"""
        if not isinstance(value, list[TypeIndicators]):
            raise TypeError("Значенням аргументу у полі indicators_type має бути значення типу list[TypeIndicators]")
        allow_values = [item.value for item in TypeIndicators]
        exist_values = [item.value for item in value]
        if not all(item in allow_values for item in exist_values):
            raise ValueError("Наявні елементи, що не дозволені у переліку типів індикаторів")
    
    @field_validator("suspicious_keywords", mode="before")
    @classmethod
    def validate_keywords_before(cls, value: TypeSuspiciousKeywords):
        """Валідація ключових слів перпеданих у поле suspicious_keywords"""
        if not isinstance(value, list[TypeSuspiciousKeywords]):
            raise TypeError("Невірний тип у полі suspicious_keywords")
        allow_values = [item.value for item in TypeSuspiciousKeywords]
        exist_values = [item.value for item in value]
        if not all(item in allow_values for item in exist_values):
            raise ValueError("Наявні елементи, що не дозволені у переліку типів ключових слів")
    
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
    filepath: str
    filesize_bytes: int
    extension: str| None = None
    created_at: datetime
    modified_at: datetime
    mimetype: str

class FileHashResult(SpecificResult):
    """Отримує хеш файлу"""
   
    algorithm: str
    value: str
    processed_bytes: int

class ExtractedStringsResult(SpecificResult):
    """Отримує рядки з файлу"""
    strings: list[str]


class SuspiciousIndicatorsResult(SpecificResult):
    """Отримує список підозрілих індикаторів з файла"""
    indicators: list[str]
    total_count: int
    


    
       