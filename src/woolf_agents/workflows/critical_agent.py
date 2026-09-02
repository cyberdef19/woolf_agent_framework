
from src.woolf_agents.domains.artifacts.schemas.contracts import CriticDecision, HistoricalResearchExecutionResult
from src.woolf_agents.llm.executor import LLMExecutor
from src.woolf_agents.workflows.state import MASAgentState
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage


class CriticalAgent:
    
    def __init__(self,
                 model: BaseChatModel,
                 executor: LLMExecutor,
                 output_schema: CriticDecision,
                 system_prompt: str
                 ):
        self._model = model 
        self._llm_with_structured_output = self._model.with_structured_output(output_schema)
        self._executor = executor
        self._system_prompt = system_prompt
    
    
    async def execute(self, state: MASAgentState)->CriticDecision:
        """Виконує критику отриманого результата після виконання плану"""
        result:HistoricalResearchExecutionResult = MASAgentState(state).get("research_result")
        user_task: str = MASAgentState(state).get("task_user")
        
        response = self._executor.model_invoke(
            self._llm_with_structured_output,
            [
                self._system_prompt,
                HumanMessage(
                    content=f"""
                         Надай критичну оцінку отриманому результату відповіді на завдання користувача.
                         Завдання користувача: {user_task}.
                         Результат відповіді: {result.model_dump_json(indent=2)}
                         Не проводь нові дослідження - ти не дослідник, але критик результату.
                    """
                    
                )
            ]
        )
        
        return response
        
        
        
        