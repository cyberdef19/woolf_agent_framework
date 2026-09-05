from typing import Self, Literal
from uuid import UUID

from pydantic import ConfigDict, Field, field_validator, model_validator, BaseModel

from src.woolf_agents.core.result import BaseExecutionResult
from .base import SpecificInput, SpecificResult, BaseTaskPlan, BasePlanStep, BaseStepResult, StepEvaluation
from enum import Enum
from datetime import datetime
from pathlib import Path
from src.woolf_agents.domains.artifacts.schemas.base import PlanStepStatus, PlanEvaluation



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

from pydantic import BaseModel, Field, model_validator


from pydantic import BaseModel, Field, field_validator, model_validator


class RetrieveHistoricalSourcesInput(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        description="Запит для семантичного пошуку в корпусі історичних джерел.",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Максимальна кількість релевантних фрагментів.",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Query cannot be empty.")

        return value


class GetAdjacentChunksInput(BaseModel):
    source_id: str = Field(
        ...,
        min_length=1,
        description="ID джерела, отриманий попереднім інструментом.",
    )

    chunk_index: int = Field(
        ...,
        ge=0,
        description="Індекс фрагмента всередині джерела.",
    )

    before: int = Field(
        default=1,
        ge=0,
        le=3,
        description="Кількість фрагментів перед цільовим.",
    )

    after: int = Field(
        default=1,
        ge=0,
        le=3,
        description="Кількість фрагментів після цільового.",
    )

    @model_validator(mode="after")
    def validate_context_window(self):
        if self.before == 0 and self.after == 0:
            raise ValueError(
                "At least one adjacent chunk must be requested."
            )

        return self


class SearchRelatedSourcesInput(BaseModel):
    source_id: str = Field(
        ...,
        min_length=1,
        description="ID вже знайденого історичного джерела.",
    )

    chunk_index: int = Field(
        ...,
        ge=0,
        description="Індекс фрагмента, для якого потрібно знайти пов'язані джерела.",
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Максимальна кількість пов'язаних фрагментів.",
    )

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Source ID cannot be empty.")

        return value


class SearchWebHistoricalSourcesInput(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        description="Пошуковий запит для пошуку історичної інформації у веб.",
    )

    max_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Максимальна кількість результатів веб-пошуку.",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Query cannot be empty.")

        return value

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


class HistoricalEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(
        description="Фактичний фрагмент або твердження, отримане з джерела"
    )

    source_id: str | None = Field(
        default=None,
        description="Ідентифікатор локального джерела"
    )

    chunk_index: int | None = Field(
        default=None,
        ge=0,
        description="Індекс фрагмента локального джерела"
    )

    source_url: str | None = Field(
        default=None,
        description="URL зовнішнього джерела"
    )

class HistoricalResearchStepResult(BaseStepResult):
    """Конкретизуючий результат кроку виконання плану"""
    evidence: list[HistoricalEvidence] = Field(
            default_factory=list,
            description="Фактичні дані, отримані під час виконання кроку"
        )
    
class SourceVerificationResult(BaseExecutionResult):
    verified: bool = Field(description="Веріфікує чи достатньо підтверджена доказова база")
    issues: list[str] = Field(default_factory=list, description="Конкретні наявні проблеми")
    supporting_sources: list[str] = Field(default_factory=list, description="Які джерела можуть підтвердити висновки")
    conflicting_sources: list[str] = Field(default_factory=list, description="Які джерела суперечать один одному")
    reason: str = Field(description="Коротке пояснення чому прийняте таке рішення")    
    
class HistoricalResearchExecutionResult(BaseExecutionResult):
    answer: str = Field(
        description="Підсумкова відповідь на дослідницьке питання."
    )

    key_findings: list[str] = Field(
        default_factory=list,
        description="Ключові встановлені результати дослідження."
    )

    uncertainties: list[str] = Field(
        default_factory=list,
        description="Невизначеності та питання, які залишилися відкритими."
    )

    sources: list[str] = Field(
        default_factory=list,
        description="Джерела, на яких ґрунтується висновок."
    )

class HistoricalResearchStepPlan(BasePlanStep):
    """Крок для дослідницького плану історичний домен"""
    research_query: str| None = Field(
        default=None,
        description=(
            "Пошуковий запит для retrieval. "
            "Заповнюй ТІЛЬКИ якщо operation='retrieve_sources'. "
            "Для extract_claims, generate_hypotheses, "
            "evaluate_hypotheses та synthesize_conclusion "
            "значення ОБОВ'ЯЗКОВО повинно бути null."
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
    

class HypothesisEvaluationStep(HistoricalResearchStepPlan):
    """Конкретний крок плану для оцінки гіпотези"""
    operation: Literal[
        "retrieve_sources",
        "extract_claims",
        "generate_hypotheses",
        "evaluate_hypotheses",
        "synthesize_conclusion"
        ] = Field(
            description="""retrieve_sources-зосередься на пошуку релевантних історичних джерел.
                           якщо джерел у контексті немає, використовуй retrieval tools.
                           extract_claims-виділяй твердження, явно підтримані отриманими джерелами.
                           generate_hypotheses-сформуй альтернативні гіпотези на основі extracted claims.
                           evaluate_hypotheses-порівняй гіпотези з supporting та contradicting evidence.
                           synthesize_conclusion-сформуй висновок, не приховуючи невизначеність і альтернативні версії.
                        """
            
        )

class HistoricalHypothesisEvaluationPlan(HistoricalResearchPlan):
    """План для оцінки історичної гіпотези"""
    steps:list[HypothesisEvaluationStep]



class EvaluationPlanContext(BaseModel):
    execution_id: UUID
    user_task: str
    evaluated_steps: list[StepEvaluation]
    resultsaechstep: list[HistoricalResearchStepResult]
    plan: HistoricalHypothesisEvaluationPlan
    human_decision: str | None = None
    interrupt_reason: str | None = None

class StepEvaluationContext(BaseModel):
    execution_id:UUID
    user_task: str
    current_step:HypothesisEvaluationStep
    current_step_result:HistoricalResearchStepResult
    human_decision: str | None = None
    interrupt_reason: str | None = None

class StepExecutionContext(BaseModel):
    user_task: str
    current_step: HypothesisEvaluationStep
    previous_results: list[HistoricalResearchStepResult]
    execution_id: UUID
    step_id: str
    step_status: PlanStepStatus

class FinalResponseContext(BaseModel):
    user_task: str
    plan_evaluation: PlanEvaluation
    final_plan: HistoricalHypothesisEvaluationPlan
    step_results: list[HistoricalResearchStepResult]
    execution_id: UUID

class CriticDecision(BaseModel):
    model_config=ConfigDict(extra="forbid")
    decision: Literal["approve", "human_decision"]
    issue: str
    recomandations: list[str] = Field(default_factory=list)
    reason: str


class HumanReviewDecision(BaseModel):
    decision: Literal[
        "approve",
        "reject",
    ]
    comment: str | None = None