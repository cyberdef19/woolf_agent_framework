from langchain.agents import create_agent 
from src.woolf_agents.llm.config import LLMSettings, LLMModel, ConfigApiKey, LLMProvider
from src.woolf_agents.llm.factory import LLMFactory
from src.woolf_agents.core.agent_spec import AgentSpec
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from .tools import get_metadata_local_file, extract_strings_local_file, hashing_local_file
from .result import AssignmentResult01
from .state import Assignment01AgentState


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

llm_with_tools = llm.bind_tools(tools=tools)
structured_llm_output = llm.with_structured_output(
    AssignmentResult01
)

def agent_node(state: Assignment01AgentState)->dict:
    """Вузол формує виклик інструментів"""
    response = llm_with_tools.invoke(
        state["messages"]
    )
    return {
        "messages":response
    }
def structured_output_node(state:Assignment01AgentState)->dict:
    """Формує структорвану відповідь"""
    response = structured_llm_output.invoke(
        state["messages"]
    )
    return {
        "structured_output": response
    }

def route_after_agent(state: Assignment01AgentState)->Literal["tools", "structured_output_node"]:
    """Обирає чи продовжувати виклики інструментів чи йти до повернення результату"""
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

graph_builder.compile()