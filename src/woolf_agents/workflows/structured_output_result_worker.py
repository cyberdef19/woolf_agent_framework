from src.woolf_agents.domains.artifacts.schemas.contracts import HistoricalResearchExecutionResult, FinalResponseContext
from .agent_worker import AbstractAgentWorker
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from src.woolf_agents.llm.executor import LLMExecutor
import json


class StructuredOutputResultWorker(
    AbstractAgentWorker[
        HistoricalResearchExecutionResult,
        FinalResponseContext
                        ]
):
    
    def __init__(self, 
                 model: BaseChatModel, 
                 executor: LLMExecutor, 
                 output_schema: HistoricalResearchExecutionResult, 
                 system_message: SystemMessage
                 ):
        super().__init__(
            model=model, 
            executor=executor, 
            output_schema=output_schema, 
            system_message=system_message
            )
    
    def _get_message(self, context: FinalResponseContext)->str:
        """Формує фінальну структуровану відповідь для користувача"""
        
        execution_id = context.execution_id
        final_plan = context.final_plan
        plan_evaluation = context.plan_evaluation
        user_task = context.user_task
        step_results = context.step_results
        
        step_results_json = [
            step_result.model_dump_json() 
            for step_result in step_results 
        ]
        
        return f"""
                Виконуємо завдання {execution_id}. Сформуй фінальну відповідь для користувача 
                після виконання завдання: {user_task}. Фінальну відповідь формуй на основі завершенного
                плану {final_plan.model_dump_json()}, на основі оцінки виконання плану: {plan_evaluation.model_dump_json()}.
                Також, візьмі до уваги результати кроків: {json.dumps(step_results_json)} 
                """
    
        