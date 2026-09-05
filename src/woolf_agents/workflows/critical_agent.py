
from src.woolf_agents.domains.artifacts.schemas.contracts import CriticDecision, HistoricalResearchExecutionResult
from src.woolf_agents.llm.executor import LLMExecutor
from src.woolf_agents.workflows.state import MASAgentState
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient



class CriticalAgent:
    
    def __init__(self,
                 model: BaseChatModel,
                 executor: LLMExecutor,
                 system_prompt: str,
                 mcp_client: MultiServerMCPClient
                 ):
        self._model = model 
        self._llm_with_structured_output = self._model.with_structured_output(CriticDecision)
        self._executor = executor
        self._system_prompt = system_prompt
        self._mcp_client = mcp_client
    
    
    async def execute(self, state: MASAgentState)->CriticDecision:
        """Виконує критику отриманого результата після виконання плану"""
        result = MASAgentState(state).get("research_result")
        user_task: str = MASAgentState(state).get("task_user")
        
        human_messages = self._mcp_client.get_prompt(
            server_name="historical",
            prompt_name="critical_review",
            arguments={
                "user_task": user_task,
                "research_result": result.model_dump_json
            }
        )
        
        response: HistoricalResearchExecutionResult = await self._executor.model_invoke(
            self._llm_with_structured_output,
            [
                self._system_prompt,
                *human_messages
                #HumanMessage(
                #    content=f"""
                #         Надай критичну оцінку отриманому результату відповіді на завдання користувача.
                #         Завдання користувача: {user_task}.
                #         Результат відповіді: {result.model_dump_json()}
                #         Не проводь нові дослідження - ти не дослідник, але критик результату.
                #    """
                    
                #)
            ]
        )
        
        return response
        
        
        
        