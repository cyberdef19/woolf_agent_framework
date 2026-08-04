from langchain.agents import create_agent 
from src.woolf_agents.llm.config import LLMSettings, LLMModel, ConfigApiKey, LLMProvider
from src.woolf_agents.llm.factory import LLMFactory
from src.woolf_agents.core.agent_spec import AgentSpec
from tests.unit.runner import AgentTestRunner, AgentTestSuiteRunner

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from .tools import get_metadata_local_file, extract_strings_local_file, hashing_local_file
from .result import AssignmentResult01
from .state import Assignment01AgentState
from .test_cases import TEST_CASES
from src.woolf_agents.workflows.tool_calling_graph import ToolCallingGraph
from src.woolf_agents.workflows.base_graph import BaseGraph
from src.woolf_agents.runtime.stop_controller import StopController
from src.woolf_agents.runtime.runner import AgentGraphRunner
from src.woolf_agents.runtime.settings import AgentRuntimeSettings
from src.woolf_agents.runtime.trajectory_logger import TrajectoryLogger
from langchain_core.messages import HumanMessage
from pathlib import Path


settings = LLMSettings(
    provider=LLMProvider.GOOGLE_GENAI,
    model = LLMModel.GEMINI25FLASH,
    api_key = ConfigApiKey.GOOGLEGEMINI
)

llm_factory = LLMFactory()
llm = llm_factory.create(settings=settings.provider)
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
    tool_names=[ get_metadata_local_file, extract_strings_local_file, hashing_local_file],
    response_language= "Українська"
) 

tool_calling_graph: BaseGraph = ToolCallingGraph(
    state=Assignment01AgentState,
    model=llm,
    tools=tools,
    output_schema=AssignmentResult01,
    system_prompt=spec.system_prompt,
    stop_controller=StopController(),  
)

compiled_graph = tool_calling_graph.build()
graph_settings = AgentRuntimeSettings()
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
                "Проаналізуй файл samples/sample.bin: "
                "отримай метадані, SHA-256, рядки "
                "та потенційні індикатори."
            )
        )
    ],
    "step_count": 0,
    "used_tokens": 0,
    "execution_status": "running",
}


async def main() -> None:
    test_runner = AgentTestRunner(
        runner=agent_graph_runner,
    )

    suite_runner = AgentTestSuiteRunner(
        test_runner=test_runner,
        output_path=Path(
            "reports/evaluation/test_results.json"
        ),
    )

    report = await suite_runner.run(
        TEST_CASES
    )

    print(
        f"Passed: {report.passed_cases}/"
        f"{report.total_cases}"
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
#result = await runner.run(initial_state=initial_state)

#structured_response = result.get(
#    "structured_response"
#)

"""llm_with_tools = llm.bind_tools(tools=tools)
structured_llm_output = llm.with_structured_output(
    AssignmentResult01
)

def agent_node(state: Assignment01AgentState)->dict:
    "Вузол формує виклик інструментів"
    response = llm_with_tools.invoke(
        state["messages"]
    )
    return {
        "messages":response
    }
def structured_output_node(state:Assignment01AgentState)->dict:
    "Формує структорвану відповідь"
    response = structured_llm_output.invoke(
        state["messages"]
    )
    return {
        "structured_output": response
    }

def route_after_agent(state: Assignment01AgentState)->Literal["tools", "structured_output_node"]:
    "Обирає чи продовжувати виклики інструментів чи йти до повернення результату"
    last_message = state["messages"][-1]
    
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return "structured_output_node"

graph_builder = StateGraph(Assignment01AgentState)
graph_builder.add_node("agent_node", agent_node)
graph_builder.add_node("tools", ToolNode(tools))
graph_builder.add_node("structured_output_node", structured_output_node)
graph_builder.add_edge(START, "agent_node")
graph_builder.add_conditional_edges(
    "agent_node", 
    route_after_agent,
    {
        "tools",
        "structured_output_node"
    }
    )
graph_builder.add_edge("tools", "agent_node")
graph_builder.add_edge("structured_output_node", END)

graph_builder.compile()"""