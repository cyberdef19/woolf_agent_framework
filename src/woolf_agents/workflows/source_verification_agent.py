
from src.woolf_agents.domains.artifacts.schemas.contracts import HistoricalResearchExecutionResult, SourceVerificationResult
from src.woolf_agents.llm.executor import LLMExecutor
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.chat_models import BaseChatModel

from src.woolf_agents.workflows.state import MASAgentState
from collections.abc import Sequence
from langchain.tools import BaseTool
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware


class SourceVerificationAgent:
    
    def __init__(
        self,
        model: BaseChatModel,
        system_prompt: str,
        mcp_client: MultiServerMCPClient,
        ):
   
        self._model = model
        self._system_prompt = system_prompt
        self._mcp_client = mcp_client
        self._tools: Sequence[BaseTool]| None = None 
        self._agent = None
    
    @property
    def tools(self) -> Sequence[BaseTool]:
        return self._tools
    
    @tools.setter
    def tools(self, tools: Sequence[BaseTool]):
        self._tools = tools
        
    def create_verification_agent(self):
        self._agent = create_agent(
            model=self._model,
            tools=self._tools,
            system_prompt=self._system_prompt,
            response_format=SourceVerificationResult,
            middleware=[
                ToolCallLimitMiddleware(
                    run_limit=3,
                    exit_behavior="continue"
                )
            ]
        )
    
    
    async def execute(self, state: MASAgentState) ->SourceVerificationResult:
        """Верифікує джерела за доказовою базою дослідження"""
        research_result:HistoricalResearchExecutionResult = MASAgentState(state).get("research_result")
        user_task: str = MASAgentState(state).get("task_user")
        resources = await self._mcp_client.get_resources(
                   "historical",
                   uris="heritage://research/methodology",
                   )

        if not resources:
            raise RuntimeError(
                "Verification methodology resource not found"
            )

        methodology = resources[0].as_string()
        messages = await self._mcp_client.get_prompt(
            "historical",
            "verification_sources",
            arguments={
                "user_task": user_task,
                "research_result": research_result.model_dump_json(),
                "methodology": methodology
            }
        )
        
        result = await self._agent.ainvoke(
            {
                "messages":messages
            }
        )
        return result["structured_response"]
        

        
        
    
    
        
        