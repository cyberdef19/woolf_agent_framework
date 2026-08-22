from uuid import uuid4
import os
from src.woolf_agents.core.agent_spec import AgentSpec
from src.woolf_agents.workflows.state import PlanExecuteState
from langchain_core.messages import HumanMessage
from src.woolf_agents.runtime.trajectory_logger import TrajectoryLogger
from src.woolf_agents.core.retry import RetryPolicyAgent, RetrySettings
from src.woolf_agents.llm.config import LLMSettings, LLMModel, ConfigGoogleAPI, LLMProvider, LangSmithSettings
from src.woolf_agents.llm.settings import url_modelrouter
from src.woolf_agents.llm.config import ConfigModelAPI, ConfigLangsmithAPI
from src.woolf_agents.llm.factory import LLMFactory
from src.woolf_agents.workflows.execute_planner_agent import ExecutePlannerAgent
from src.woolf_agents.core.result import BaseExecutionResult
from assignments.assignment_02.contracts import HistoricalHypothesisEvaluationPlan
from src.woolf_agents.domains.artifacts.schemas.base import StepEvaluation, PlanEvaluation, PlanStepStatus
from src.woolf_agents.domains.artifacts.schemas.contracts import StepExecutionContext
from src.woolf_agents.runtime.stop_controller import StopController
from src.woolf_agents.llm.executor import LLMExecutor
from src.woolf_agents.workflows.base_graph import BaseGraph
from src.woolf_agents.runtime.runner import AgentGraphRunner
from src.woolf_agents.runtime.settings import AgentRuntimeSettings
from src.woolf_agents.infrastructure.vectorstore.factory import VectorStoreFactory
from src.woolf_agents.infrastructure.vectorstore.basedb import MultiligualE5Embedding
from src.woolf_agents.domains.artifacts.services.services import (
    HistoricalRetrieverService, 
    HistoricalIngestionService,
    ingest_all_sources
)
from langchain_core.documents import Document
from src.woolf_agents.data.historical_sources.sources import metadata_sources
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import aiosqlite

from pathlib import Path

import asyncio

embeddings = MultiligualE5Embedding()
vector_base = VectorStoreFactory.create(provider="chroma",model_embedding=embeddings) 
retrieval_service = HistoricalRetrieverService(vector_store=vector_base)

@tool
async def retrieve_historical_sources(
    query: str,
    top_k: int = 5,
) -> list:
    """
    Пошук релевантних фрагментів історичних джерел
    у локальній векторній базі.

    Використовуй інструмент, коли для виконання поточного
    кроку потрібні фактичні дані з корпусу історичних джерел.
    """

    return await retrieval_service.search(
        query=query,
        top_k=top_k,
    )

settings = LLMSettings(
    provider=LLMProvider.OPENROUTER,
    model = LLMModel.GOOGLEGEMMA426BA4B,
    base_url=url_modelrouter["openrouter_url"],
    api_key = ConfigModelAPI.OPENROUTERKEY
)
llm = LLMFactory.create(settings=settings)
tools = [retrieve_historical_sources]

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
        "retrieve_historical_sources",
    ),

    response_language="Українська",
)

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
    "user_task": "Яке походження назви Хаджибей? Визнач представлені в доступних джерелах гіпотези та оціни, яка з них має найкращу доказову підтримку.",
    "execution_id":str(uuid4()),
    "step_messages_start_idx": 0,
    
    
}


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
    plan_executor = ExecutePlannerAgent(
        state_schema=PlanExecuteState,
        model=llm,
        output_schema=BaseExecutionResult,
        plan_schema=HistoricalHypothesisEvaluationPlan,
        step_evaluate_schema=StepEvaluation,
        plan_evaluation=PlanEvaluation,
        tools=tools,
        system_prompt=spec.system_prompt,
        stop_controller=StopController(),
        executor=LLMExecutor(retry_agent=retry_policy, llm_timeout_seconds=settings.llm_timeout_seconds),
        checkpointer=checkpointer
    )

    compiled_graph = plan_executor.build()
    graph_settings = AgentRuntimeSettings(timeout_seconds=420)
    agent_graph_runner = AgentGraphRunner(
        graph=compiled_graph,
        settings=graph_settings,
        stop_controller=StopController(),
        trajectory_logger=TrajectoryLogger(graph_settings.trajectory_log_directory)
    )


    ingestion_service = HistoricalIngestionService(vector_store=vector_base)
    #await ingest_all_sources(
    #    service=ingestion_service,
    #    sources=metadata_sources,
    #    base_dir=Path(
    #        "I:\\WoolfFrameworkAgent\\src\\woolf_agents\\data\\historical_sources"
    #   ))

    thread_id = str(uuid4())

    result = await agent_graph_runner.run(
        initial_state=initial_state,
        thread_id=thread_id
        )
    
    interrupts = result.get("__interrupt__", [])
    if interrupts:
        interrupt_data = interrupts[0].value

        print("\n=== HUMAN IN THE LOOP ===")
        print(interrupt_data["reason"])
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

    

if __name__=="__main__":
    asyncio.run(main())
