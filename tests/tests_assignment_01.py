from pathlib import Path
import pytest
from tests.unit.runner import AgentTestRunner, AgentTestSuiteRunner
from src.woolf_agents.core.retry import RetryPolicyAgent, RetrySettings
from src.woolf_agents.llm.executor import LLMExecutor
from tests.unit.test_case import AgentTestCase, AgentTestExpectation
from src.woolf_agents.runtime.runner import AgentGraphRunner
from src.woolf_agents.runtime.settings import AgentRuntimeSettings
from src.woolf_agents.runtime.trajectory_logger import TrajectoryLogger
from src.woolf_agents.runtime.stop_controller import StopController
from assignments.assignment_01.result import AssignmentResult01
from assignments.assignment_01.state import Assignment01AgentState
from src.woolf_agents.workflows.tool_calling_graph import ToolCallingGraph
from src.woolf_agents.workflows.base_graph import BaseGraph
from assignments.assignment_01.tools import get_metadata_local_file, extract_strings_local_file, hashing_local_file
from src.woolf_agents.llm.config import LLMSettings, LLMModel, ConfigGoogleAPI, LLMProvider, ConfigModelAPI
from src.woolf_agents.llm.settings import url_modelrouter
from src.woolf_agents.llm.factory import LLMFactory
from src.woolf_agents.core.agent_spec import AgentSpec


TEST_CASES = [
    AgentTestCase(
        case_id="metadata_only",
        input_query=(
            f"Отримай лише метадані запропонованого файла "
        ),
        artifact_path= Path(
            "I:\\WoolfFrameworkAgent\\artifact_sample.bin"
        ),
        expected_result=(
            "Агент повинен викликати лише інструмент "
            "отримання метаданих і повернути відомості "
            "про файл."
        ),
        expectation=AgentTestExpectation(
            required_tools=(
                "get_metadata_local_file",
            ),
            forbidden_tools=(
              "extract_strings_local_file", 
              "hashing_local_file"
            ),
            expected_status="completed",
        ),
    ),
    AgentTestCase(
        case_id="sha256_hash",
        input_query=(
            "Обчисли SHA-256 запропонованого файла "
        ),
        artifact_path= Path(
                "I:\\WoolfFrameworkAgent\\artifact_sample.bin"
            ),
        expected_result=(
            "Агент повинен викликати calculate_hash "
            "з алгоритмом SHA-256."
        ),
        expectation=AgentTestExpectation(
            required_tools=(
                "hashing_local_file",
            ),
            forbidden_tools=(
                          "extract_strings_local_file", 
                          "get_metadata_local_file"
                        ),
            expected_status="completed",
            expected_content=(
                "sha256",
            ),
        ),
    ),
    AgentTestCase(
        case_id="extract_strings",
        input_query=(
            "Витягни читабельні текстові рядки з запропонованого файла "
        ),
         artifact_path= Path(
            "I:\\WoolfFrameworkAgent\\artifact_sample.bin"
                ),
        expected_result=(
            "Агент повинен використати інструмент "
            "витягування рядків."
        ),
        expectation=AgentTestExpectation(
            required_tools=(
                "extract_strings_local_file",
            ),
            forbidden_tools=(
                    "hashing_local_file", 
                    "get_metadata_local_file"
                                    ),
            expected_status="completed",
        ),
    ),
    AgentTestCase(
            case_id="full_analysis",
            input_query=(
                "Проведи первинний аналіз запропонованого файла: "
                " отримай метадані, SHA-256, рядки."
            ),
            artifact_path= Path(
                        "I:\\WoolfFrameworkAgent\\artifact_sample.bin"
                    ),
            expected_result=(
                "Агент повинен використати всі три "
                "інструменти й сформувати структурований звіт."
            ),
            expectation=AgentTestExpectation(
                required_tools=(
                   "extract_strings_local_file",
                   "hashing_local_file", 
                   "get_metadata_local_file"
                ),
                expected_status="completed",
            ),
        ),

    
]

settings = LLMSettings(
    provider=LLMProvider.OPENROUTER,
    model = LLMModel.GPTOSS20bFREE,
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
                  "Узагальнюй, підсумовуй важливі висновки після отримання результату від інструмента"
                  ),
    constraints=(
                 "Не вигадуй метадані, хеші, рядки чи індикатори",
                 "Не класифікуй індикатори як шкідливі без підтверджуючих доказів",
                 "Не отримуй доступ до інших файлів, окрім наданого локального файлу користувачем",
                 "Не модифікуй файл, надайний на аналіз"
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
graph_settings = AgentRuntimeSettings()
agent_graph_runner = AgentGraphRunner(
    graph=compiled_graph,
    settings=graph_settings,
    stop_controller=StopController(),
    trajectory_logger=TrajectoryLogger(graph_settings.trajectory_log_directory)
)

@pytest.mark.asyncio
async def test_assignment_01_agent() -> None:
    test_runner = AgentTestRunner(
        runner=agent_graph_runner,
    )

    suite_runner = AgentTestSuiteRunner(
        test_runner=test_runner,
        output_path=Path(
            "test_result.json"
        ),
    )

    report = await suite_runner.run(
        TEST_CASES
    )

    assert report.total_cases == len(TEST_CASES)
    assert report.passed_cases == report.total_cases
    assert report.failed_cases == 0


