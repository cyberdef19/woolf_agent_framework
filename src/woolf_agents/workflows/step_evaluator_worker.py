from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from src.woolf_agents.domains.artifacts.schemas.contracts import StepEvaluationContext, StepEvaluation
from .agent_worker import AbstractAgentWorker
from src.woolf_agents.llm.executor import LLMExecutor

class StepEvaluatorWorker(
    AbstractAgentWorker[ 
        StepEvaluation,
        StepEvaluationContext
    ]
):
    
    def __init__(self, 
                 model: BaseChatModel,
                 executor: LLMExecutor,
                 system_message: SystemMessage,
                 output_schema: StepEvaluation
                 ):
        super().__init__(
            model=model,
            executor=executor,
            system_message=system_message,
            output_schema=output_schema
        )
    
    def _get_message(self, context: StepEvaluationContext)->str:
        """Формує повідомлення для мовленевої моделі для оцінки кроку плану"""
        current_step = StepEvaluationContext(context).current_step
        expected_result =current_step.expected_result
        task_step = current_step.objective
        current_step_result = StepEvaluationContext(context).current_step_result
        task_step_result = current_step_result.summary
        execution_id = StepEvaluationContext(context).execution_id
        
        return f"""
                   Виконання завдання: {execution_id}. Оціни результат кроку виконання плану.
                   Завдання кроку: {task_step}.
                   Отриманий результат виконання кроку: {task_step_result}.
                   Очікуваний результат виконання кроку: {expected_result}.
                   """
       
        
        
        
        