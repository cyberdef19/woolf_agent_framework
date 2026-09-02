
import asyncio
import os
from uuid import uuid4

import aiosqlite

from src.woolf_agents.core.agent_spec import AgentSpec
from src.woolf_agents.core.retry import RetryPolicyAgent, RetrySettings
from src.woolf_agents.domains.artifacts.schemas.base import PlanEvaluation, PlanStepStatus, StepEvaluation
from src.woolf_agents.domains.artifacts.schemas.contracts import HistoricalHypothesisEvaluationPlan, HistoricalResearchExecutionResult, HistoricalResearchStepResult, StepExecutionContext
from src.woolf_agents.llm.config import ConfigLangsmithAPI, LangSmithSettings, url_modelrouter, ConfigModelAPI, LLMModel, LLMProvider, LLMSettings
from src.woolf_agents.llm.executor import LLMExecutor
from src.woolf_agents.llm.factory import LLMFactory
from src.woolf_agents.runtime.runner import AgentGraphRunner
from src.woolf_agents.runtime.settings import AgentRuntimeSettings
from src.woolf_agents.runtime.stop_controller import StopController
from src.woolf_agents.runtime.trajectory_logger import TrajectoryLogger
from src.woolf_agents.tools.retriever_tools import get_adjacent_chunks, retrieve_historical_sources, search_related_sources
from src.woolf_agents.tools.web_retriever_tools import search_web_historical_sources
from src.woolf_agents.workflows.multiagent_planner_execute_graph import MultiAgentPlannerExecuteGraph
from src.woolf_agents.workflows.plan_evaluator_worker import PlanEvaluatorWorker
from src.woolf_agents.workflows.reasoning_worker import ReasoningWorker
from src.woolf_agents.workflows.state import PlanExecuteState, PlanExecuteStatus, SourceInterrupt, ToolGraphState
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from src.woolf_agents.workflows.step_evaluator_worker import StepEvaluatorWorker
from src.woolf_agents.workflows.structured_output_result_worker import StructuredOutputResultWorker
from src.woolf_agents.workflows.tool_calling_worker import ToolCallingWorker


settings = LLMSettings(
    provider=LLMProvider.OPENROUTER,
    model = LLMModel.GPTOMINI4O,
    base_url=url_modelrouter["openrouter_url"],
    api_key = ConfigModelAPI.OPENROUTERKEY
)
llm = LLMFactory.create(settings=settings)
tools = [
    retrieve_historical_sources, 
    get_adjacent_chunks, 
    search_web_historical_sources, 
    search_related_sources
    ]

retry_policy = RetryPolicyAgent(
    settings=RetrySettings()
)

spec = AgentSpec(
    name="Historical Research Agent",

    role=(
        "Спеціалізуєшся на дослідженні історичних питань, "
        "аналізі історичних джерел, формуванні альтернативних "
        "гіпотез та їх аргументованому порівнянні."
    ),

    goal=(
        "Досліджувати історичні питання на основі доступних джерел, "
        "виділяти підтверджені твердження, формувати та порівнювати "
        "альтернативні історичні гіпотези і створювати обґрунтовані "
        "висновки із збереженням невизначеності та суперечливості "
        "доказової бази."
    ),

    instructions=(
        "Використовуй доступні історичні джерела як основну доказову "
        "базу для фактичних тверджень.",

        "Чітко відокремлюй інформацію, отриману з джерел, від "
        "інтерпретацій та висновків.",

        "Враховуй альтернативні історичні версії та не відкидай "
        "гіпотези без достатніх підстав.",

        "Порівнюй гіпотези за наявними підтверджуючими та "
        "суперечливими свідченнями.",

        "Враховуй походження, релевантність та незалежність джерел "
        "під час оцінювання доказової бази.",

        "Явно зазначай недостатність, суперечливість або "
        "невизначеність доступних даних.",

        "Використовуй доступні інструменти отримання джерел, "
        "коли для виконання поточного завдання бракує фактичних даних.",

        "Формуй висновки лише в межах доказів та результатів, "
        "доступних у поточному контексті виконання.",
    ),

    constraints=(
        "Не вигадуй історичні факти, джерела, цитати, авторів, "
        "дати або археологічні свідчення.",

        "Не представляй припущення або інтерпретацію як встановлений факт.",

        "Не приховуй суттєві суперечності між джерелами або "
        "альтернативними історичними версіями.",

        "Не вважай кілька фрагментів одного джерела незалежними "
        "підтвердженнями.",

        "Не роби категоричного висновку, якщо наявна доказова база "
        "не дозволяє достатньо обґрунтовано обрати між альтернативними "
        "гіпотезами.",

        "Не використовуй недоступні або неперевірені джерела так, "
        "ніби їх зміст був фактично отриманий системою.",

        "Не змінюй зміст отриманих історичних свідчень для "
        "підтвердження бажаної гіпотези.",
    ),

    tool_names=(
        """
        retrieve_historical_sources, 
        get_adjacent_chunks, 
        search_web_historical_sources,
        search_related_sources
        
        """,
    ),

    response_language="Українська",
)
user_task = "Яке походження назви Хаджибей? Визнач представлені в доступних джерелах гіпотези та оціни, яка з них має найкращу доказову підтримку."
initial_state: PlanExecuteState = {
    "messages": [
        HumanMessage(
            content=(
                "Яке походження назви Хаджибей? "
                "Визнач представлені в доступних джерелах "
                "гіпотези та оціни, яка з них має найкращу "
                "доказову підтримку."
            )
        )
    ],
    "step_count": 0,
    "used_tokens": 0,
    "execution_status": PlanStepStatus.PENDING,
    "current_step_idx": 0,
    "current_step_result": None,
    "errors": [],
    "evaluated_current_step": None,
    "evaluated_steps":[],
    "executor_response": None,
    "len_steps": 0,
    "metadata": {},
    "plan": None,
    "plan_execution_evaluated": None,
    "results": [],
    "revised_plans":[],
    "structured_response": None,
    "user_task": user_task,
    "execution_id":str(uuid4()),
    "step_messages_start_idx": 0,
    "human_deсision": None,
    "interrupt_reason": None,
    "source_interrupt": SourceInterrupt.NO_SOURCE,
    
    
}

EVALUATION_SYSTEM_PROMPT = """
ПРАВИЛА ПРИЙНЯТТЯ РІШЕННЯ

Твоя задача — визначити, чи достатній результат поточного кроку
для продовження виконання плану.

CONTINUE є основним рішенням.

Поверни CONTINUE, якщо:
- основна мета поточного кроку досягнута;
- отримано інформацію, достатню для виконання наступного кроку;
- результат може бути неповним, але його неповнота не блокує подальше дослідження;
- існує невизначеність або суперечності, але вони можуть бути збережені
  як частина дослідницького результату;
- додатковий пошук міг би покращити результат, але не є необхідним
  для продовження плану.

Не вимагай повної, вичерпної або беззаперечної відповіді.
Історичне дослідження може містити неповні, суперечливі
або неоднозначні свідчення.

REPLAN дозволений ТІЛЬКИ якщо результат кроку показує,
що поточний план більше не може привести до мети дослідження.

INTERRUPT дозволений ТІЛЬКИ якщо для продовження необхідне рішення
користувача, яке система принципово не може прийняти самостійно.

Не використовуй INTERRUPT лише через недостатню кількість джерел,
низьку впевненість, суперечливі джерела або можливість покращити результат.

Якщо поточний результат дозволяє перейти до наступного кроку,
ОБОВ'ЯЗКОВО поверни CONTINUE.
"""


def configure_langsmith(
    settings: LangSmithSettings,
) -> None:

    if not settings.enabled:
        os.environ["LANGSMITH_TRACING"] = "false"
        return

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.api_key
    os.environ["LANGSMITH_PROJECT"] = settings.project
    os.environ["LANGSMITH_ENDPOINT"] = settings.endpoint

async def main()->None:
    
    configure_langsmith(
        settings=LangSmithSettings(
            enabled=True,
            api_key=ConfigLangsmithAPI.LANGSMITHKEY,
            project="HistoricalHypothesisAgent"
        )
    )
    
    connection = await aiosqlite.connect(
        "src\\woolf_agents\\data\checkpoints\\checkpoints.sqlite"
    )
    checkpointer = AsyncSqliteSaver(
        connection
    )
    
    executor = LLMExecutor(retry_agent=retry_policy, llm_timeout_seconds=settings.llm_timeout_seconds)
    
    tool_settings = LLMSettings(
        provider=LLMProvider.OPENROUTER,
        model = LLMModel.GPTOMINI4O,
        base_url=url_modelrouter["openrouter_url"],
        api_key = ConfigModelAPI.OPENROUTERKEY
        )
    eval_settings = LLMSettings(
            provider=LLMProvider.OPENROUTER,
            model = LLMModel.GPTOMINI4O,
            base_url=url_modelrouter["openrouter_url"],
            api_key = ConfigModelAPI.OPENROUTERKEY
            )
    workers = {
        "tool_worker": ToolCallingWorker(
            state=ToolGraphState,
            llm=LLMFactory.create(settings=tool_settings),
            output_schema=HistoricalResearchStepResult,
            system_prompt=spec.system_prompt,
            executor=executor,
            stop_controller=StopController(),
            checkpointer=checkpointer,
            tools=tools
        ),
        "reasoning_worker":ReasoningWorker(
            model=llm,
            output_schema=HistoricalResearchStepResult,
            executor=executor,
            system_message=spec.system_prompt
            ),
        "step_evaluating_worker": StepEvaluatorWorker(
            model=LLMFactory.create(settings=eval_settings),
            executor=executor,
            system_message=EVALUATION_SYSTEM_PROMPT,
            output_schema=StepEvaluation
            ),
        "evaluating_worker": PlanEvaluatorWorker(
            model=LLMFactory.create(settings=eval_settings),
            executor=executor,
            system_message=EVALUATION_SYSTEM_PROMPT,
            output_schema=PlanEvaluation
        ),
        "structured_output_worker": StructuredOutputResultWorker(
            model=llm,
            executor=executor,
            system_message=spec.system_prompt,
            output_schema=HistoricalResearchExecutionResult
        )
    }
    plan_executor = MultiAgentPlannerExecuteGraph(
         state_schema=PlanExecuteState,
         model=llm,
         output_schema=HistoricalResearchExecutionResult,
         system_prompt=spec.system_prompt,
         executor=LLMExecutor(retry_agent=retry_policy, llm_timeout_seconds=settings.llm_timeout_seconds),
         stop_controller=StopController(),
         checkpointer=checkpointer,
         workers=workers,
         plan_schema=HistoricalHypothesisEvaluationPlan,
         tools=tools   
    )
    plan_executor_compiled = plan_executor.build()
    agent_settings = AgentRuntimeSettings(timeout_seconds=420)
    agent_graph_runner = AgentGraphRunner(
        graph=plan_executor_compiled,
        settings=agent_settings,
        stop_controller=StopController(),
        trajectory_logger=TrajectoryLogger(agent_settings.trajectory_log_directory)
    )
    
    thread_id = str(uuid4())
    
    result = await agent_graph_runner.run(
            initial_state=initial_state,
            thread_id=thread_id
            )
        

    if result.get("execution_status") == PlanExecuteStatus.WAITTING_FOR_HUMAN:
    
        print("\n=== HUMAN IN THE LOOP ===")
        print(result.get("interrupt_reason"))
        print("1 - Продовжити")
        print("2 - Скасувати")
    
        answer = input("Ваш вибір: ")
    
        decision = (
                "approve"
                if answer == "1"
                else "cancel"
            )
    
        result = await agent_graph_runner.resume(
                thread_id=thread_id,
                decision=decision,
            )
    
    structured_response = result.get(
            "structured_response"
            )
    
    
    print("Завдання користувача")
    print(user_task)
    print(f"Статус: {structured_response["status"]}")
    print(f"Загальний висновок: {structured_response["summary"]}")
    print(f"Ключові знахідки: {structured_response["key_findings"]}")
    print(f"Обмеження: {structured_response["uncertainties"]}")
    
    
        
    
if __name__=="__main__":
    asyncio.run(main())
    
    
    
    


