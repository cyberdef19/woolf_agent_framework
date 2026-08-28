from pydantic import BaseModel, ConfigDict, Field, field_validator
from pathlib import Path
from enum import StrEnum
from typing import TypeVar, Generic
from pydantic import BaseModel, ConfigDict
from src.woolf_agents.core.errors import ErrorInfo


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
#!----------------------------------------Сутності планувальника--------------------------------------------

class PlanStepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class BasePlanStep(BaseModel):
    """Спільний загальний клас для одного кроку плана"""
    model_config = ConfigDict(
                extra="forbid"
            )  
    
    id: str = Field(
        description="ID ідентифікатор кроку плана"
    )
    step_status: PlanStepStatus = Field(
        description="Статус виконання кроку плану"
    )
    objective: str = Field(
        description="Об'єктивне конкретне завдання кроку"
    )
    expected_result: str = Field(
        description="Очікуваний результат від виконання кроку завдання"
    )
    require_tools: bool = Field(
        default=False,
        description="Визначає чи треба викликати інструменти для реалізації кроку плану"
    )
    require_reasoning: bool = Field(
        default=False,
        description="Визначає чи потрібно reasoning (міркування) для виконання кроку"
    )
    require_evaluation: bool = Field(
        default=False,
        description="Визначає чи потрібна оцінка кроку плану для визначення якості виконання кроку"
    )
    
    
class BaseTaskPlan(BaseModel):
    """Спільний загальний клас для планування"""
    model_config = ConfigDict(
                extra="forbid"
            )  
    
    goal: str = Field(
        description="Мета планування"
    )  
    steps: list[BasePlanStep] = Field(
        description="Список кроків плану"
    )      
 

    
class BaseStepResult(BaseModel):
    """Результат окремого крока планувальника"""
    model_config=ConfigDict(
        extra="forbid"
    )
    step_id: str = Field(
        description="Ідентифікатор кроку"
    )       
    summary: str = Field(
        description="Підсумок для окремого крока"
    )
    errors: list[ErrorInfo] = Field(
        default_factory=list,
        description="Помилки, що виникли за час виконання кроку планування"
    )
    
class StepDecision(StrEnum):
    """Можливе рішення після виконання оцінки кроку плана"""

    CONTINUE = "continue"
    REPLAN = "replan"
    INTERRUPT = "interrupt"
    FAIL = "fail"


class StepEvaluation(BaseModel):
    """
    Структурована оцінка результату після виконання кроку плану
    Визначає чи буде виконуваний план продовжувати виконання без змін
    чи буде скоригований.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    step_id: str = Field(
        description=(
           "Ідентифікатор кроку плана відповідає id кроку плана BasePlanStep"
        )
    )

    objective_satisfied: bool = Field(
        description=(
            "True якщо знайдений результат дійсно відповідає визначеному"
            "завданням результату. False якщо результат "
            "неповний, не відповідає дійсності або ж рішення взагалі відсутнє по кроку."
        )
    )

    sufficient_for_next_step: bool = Field(
        description=(
            "True якщо має достатньо інформації, щоб перейти до наступного кроку плану."
            "False якщо результат неповний і план слід підкоригувати, щоб добитися надійнішої відповіді"
        )
    )

    contradictions_detected: bool = Field(
        description=(
            "True якщо в отриманому результаті містяться суттєві суперечності"
        )
    )

    new_information_changes_plan: bool = Field(
        description=(
            "True якщо отримана нова інформація під час виконання кроку плану"
            "робе необхідним перепланувати план, бо наступні кроки виявляються"
            "недостатніми для отримання релевантного результату"
        )
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Рівень впевненості в оцінці між 0.0 to 1.0. "
            "Використовуй низьке значення впевненості, якщо є невизначеність у відповіді, "
            "неповна відповідь, суперечлива або ж її важко цінити. Низьке значення показника"
            "означає, що доцільність рішення про продовження плану не є рекомендованим рішенням"
            "Даний показник не є мірою успішності виконання кроку."
        )
    )

    decision: StepDecision = Field(
        description=(
            "Рекомендована дія в потоці виконання. "
            "'continue' якщо план продовжує виконуватися без змін; "
            "'replan' якщо план вимагає подальшого уточнення, перепланування; "
            "'interrupt' якщо вимагається втручання людини human-in-the-loop; "
            "'fail' якщо виконання плану з якоїсь причини не може бути продовжено."
        )
    )

    reason: str = Field(
        description=(
            "Пояснює чому саме таке рішення обрано посилайся на конкретні деталі,"
            "характеристики мети очікуваного етапу виконання плану, замість надання"
            "загальної характеристики."
        )
    )
class PlanDecisionStatus(StrEnum):
    COMPLETE = "complete"
    REPLAN = "replan"
    INTERRUPT = "interrupt"
    FAIL = "fail"
    
class PlanEvaluation(BaseModel):
    """
    Структурована оцінка виконуваного плану на основі поточного плану
    списку оцінок по кроку та списку результатів по крокам
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
    )

    goal_satisfied: bool = Field(
        description=(
            "True якщо усі в совокупності результати кроків плану"
            "в достатній мірі задовольняють мету завдання"
        )
    )

    task_answerable: bool = Field(
        description=(
            "True якщо доступні результати надають можливість" 
            "отримати завершену повну відповідь. "
        )
    )

    evidence_sufficient: bool = Field(
        description=(
            "True якщо накопичені проміжні результати та докази "
            "є достатніми для обгрунтування висновку"
            "без потреби в додаткових дослідженнях"
        )
    )

    internal_consistency: bool = Field(
        description=(
            "True якщо отримані результати кроків є взаємно сумісними"
            "та відсутні суперечливості - наявні суперечності були опрацьовані"
        )
    )

    unresolved_contradictions: bool = Field(
        description=(
            "True якщо суттєві суперечності залишаються невирішеними"
            "та істотно впливають на виконання завдання."
        )
    )

    missing_information: bool = Field(
        description=(
            "True якщо після виконання плану відсутня важлива інформація, яка"
            "яка є необхідною для створення загального висновку і досягнення мети."
        )
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            """ Впевненість в правильності оцінки загального виконання плану та в правильності
            прийнятого рішення"""
            
        )
    )

    decision: PlanDecisionStatus = Field(
        description=(
            "Рекомендація для виконання workflow "
            "'complete' означає що мета повністю досягнена потік виконання може бути фіналізований; "
            "'replan' необхідність відправити поточний план на перепланування; "
            "'interrupt' перед продовженням виконання необхідне втручання людини; "
            "'fail' поточне завдання не може бути виконано в силу недоступності якихось властивостей або інформації"
        )
    )

    reason: str = Field(
        description=(
            """Стисле пояснення причин обраного рішення
            грунтується на вихідному завданні, плані, результатів по крокам
            та оціночних показників по крокам"""
            
        )
    )
    
