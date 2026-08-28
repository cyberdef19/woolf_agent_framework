from langchain_core.language_models.chat_models import BaseChatModel
from src.woolf_agents.llm.executor import LLMExecutor
from src.woolf_agents.domains.artifacts.schemas.contracts import StepExecutionContext, HistoricalResearchStepResult
from langchain_core.messages import  SystemMessage
from .agent_worker import AbstractAgentWorker
import json


class ReasoningWorker(
    AbstractAgentWorker[
        HistoricalResearchStepResult,
        StepExecutionContext
    ]
):
    
    def __init__(self,
                 model: BaseChatModel,
                 executor: LLMExecutor,
                 output_schema: HistoricalResearchStepResult,
                 system_message: SystemMessage):
         super().__init__(
             model=model,
             executor=executor,
             output_schema=output_schema,
             system_message=system_message
         )
    
    def _get_message(self, context: StepExecutionContext)-> str:
        """Повертає повідомлення до мовленевої моделі для міркування"""
        user_task = StepExecutionContext(context).user_task
        step_status = StepExecutionContext(context).step_status
        step_id = StepExecutionContext(context).step_id
        previous_results = StepExecutionContext(context).previous_results
        execution_id = StepExecutionContext(context).execution_id
        current_step = StepExecutionContext(context).current_step
        
        previuos_results_json = [
            result.model_dump_json() 
            for result in previous_results
        ]
        
        return f"""
                Виконання завдання з ідентифікатором {execution_id}. 
                Виконай міркування з метою вирішити конкретне підзавдання плану. 
                План складається з цілого ряда кроків. Поточний крок плану {step_id}.
                Поточний крок плану у рамках загального завдання користувача. 
                Ось завдання користувача: {user_task}.
                Ось поточний крок плану: {current_step.model_dump_json()}
                Ось результати виконання попередніх кроків: {json.dump(previuos_results_json)}
        """
        
        
        