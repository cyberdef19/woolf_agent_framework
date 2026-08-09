from langchain.agents import create_agent 
from src.woolf_agents.llm.config import LLMSettings, LLMModel, ConfigGoogleAPI, LLMProvider
from src.woolf_agents.llm.factory import LLMFactory
from src.woolf_agents.core.agent_spec import AgentSpec
from src.woolf_agents.core.retry import RetryPolicyAgent, RetrySettings
from src.woolf_agents.llm.executor import LLMExecutor
from assignments.assignment_01.result import AssignmentResult01
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from assignments.assignment_01.tools import get_metadata_local_file, extract_strings_local_file, hashing_local_file
from src.woolf_agents.core.result import BaseExecutionResult
from assignments.assignment_01.state import Assignment01AgentState
from src.woolf_agents.workflows.tool_calling_graph import ToolCallingGraph
from src.woolf_agents.workflows.base_graph import BaseGraph
from src.woolf_agents.runtime.stop_controller import StopController
from src.woolf_agents.runtime.runner import AgentGraphRunner
from src.woolf_agents.runtime.settings import AgentRuntimeSettings
from src.woolf_agents.runtime.trajectory_logger import TrajectoryLogger
from langchain_core.messages import HumanMessage
from pathlib import Path
from src.woolf_agents.llm.settings import url_modelrouter
from src.woolf_agents.llm.config import ConfigModelAPI
import asyncio


settings = LLMSettings(
    provider=LLMProvider.OPENROUTER,
    model = LLMModel.GOOGLEGEMMA426BA4BFREE,
    base_url=url_modelrouter["openrouter_url"],
    api_key = ConfigModelAPI.OPENROUTERKEY
)

#llm_factory = LLMFactory()
llm = LLMFactory.create(settings=settings)
tools = [get_metadata_local_file, extract_strings_local_file, hashing_local_file]

spec = AgentSpec(
    name="Artifact Analysis Agent",
    role="Спеціалізуєшся на цифровій форензиці, базовий аналіз локальних файлів",
    goal="Збирати, витягувати інформацію з цифрових артефактів і надавати\
          зібрану інформацію в стислому вигляді як доказову базу",
    instructions=("Використовуй доступні інструменти, якщо потрібні дані файлу",
                  "Обирай лише необхідні інструменти, щоб задовольнити вимоги користувача",
                  "Роби висновки лише виходячи з отриманих результатів інструментів",
                  "Чітко відрізняй отримані індикатори від шкідливої активності",
                  "Узагальнюй, підсумовуй важливі висновки після отримання результату від інструмента",
                  "Твоє завдання вирішити який інструмент обрати та інтерпретувати результат",
                  ),
    constraints=(
                 "Не вимагай у користувача надати файл на дослідження",
                 "Завжди використовуй tools для аналізу локальних файлів"
                 "Не вигадуй метадані, хеші, рядки чи індикатори",
                 "Не класифікуй індикатори як шкідливі без підтверджуючих доказів",
                 "Не отримуй доступ до інших файлів, окрім наданого локального файлу користувачем",
                 "Не модифікуй файл, надайний на аналіз",
                 "Вважай, що надайний файл вже достуний для аналізу"
                ),
    tool_names=(
        "get_metadata_local_file", 
        "extract_strings_local_file", 
        "hashing_local_file"
        ),
    response_language= "Українська"
) 
retry_policy = RetryPolicyAgent(
    settings=RetrySettings()
)

tool_calling_graph: BaseGraph = ToolCallingGraph(
    state=Assignment01AgentState,
    model=llm,
    tools=tools,
    output_schema=AssignmentResult01,
    system_prompt=spec.system_prompt,
    stop_controller=StopController(), 
    executor= LLMExecutor(retry_agent=retry_policy, llm_timeout_seconds=settings.llm_timeout_seconds)
)

compiled_graph = tool_calling_graph.build()
graph_settings = AgentRuntimeSettings(timeout_seconds=6000)
agent_graph_runner = AgentGraphRunner(
    graph=compiled_graph,
    settings=graph_settings,
    stop_controller=StopController(),
    trajectory_logger=TrajectoryLogger(graph_settings.trajectory_log_directory)
)
initial_state: Assignment01AgentState = {
    "messages": [
        HumanMessage(
            content=(
                "Проаналізуй файл I:\\WoolfFrameworkAgent\\artifact_sample.bin"
                "отримай метадані, SHA-256, отримай рядки запропонованого файла"
            )
        )
    ],
    "step_count": 0,
    "used_tokens": 0,
    "execution_status": "running",
    "artifact_path": Path(
        "I:\\WoolfFrameworkAgent\\artifact_sample.bin"
    )
}

async def main()->None:

    result = await agent_graph_runner.run(initial_state=initial_state)

    structured_response = result.get(
        "structured_response"
        )
    print(f"Результат: status {structured_response["status"]}")
    print(f"Підсумок: summary {structured_response["summary"]}")
    print(f"Метадані: {structured_response["metadata"]}")
    print(f"Хеш-файла: {structured_response["filehash"]}")
    print(f"Рядки з байтового файла: {structured_response["extracted_strings"]}")
    

if __name__=="__main__":
    asyncio.run(main())

