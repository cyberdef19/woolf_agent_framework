from langchain_core.language_models.chat_models import BaseChatModel
from src.woolf_agents.llm.executor import LLMExecutor
from src.woolf_agents.domains.artifacts.schemas.contracts import EvaluationPlanContext
from src.woolf_agents.domains.artifacts.schemas.base import PlanEvaluation
from langchain_core.messages import  SystemMessage
from .agent_worker import AbstractAgentWorker
import json

class PlanEvaluatorWorker(
    AbstractAgentWorker[
    PlanEvaluation,
    EvaluationPlanContext
    ]
):
    def __init__(self, 
                model: BaseChatModel, 
                executor: LLMExecutor, 
                output_schema: PlanEvaluation, 
                system_message: SystemMessage
                ):
      super().__init__(
          model=model, 
          executor=executor, 
          output_schema=output_schema, 
          system_message=system_message
          )
      
    def _get_message(self, context: EvaluationPlanContext)->str:
        execution_id = EvaluationPlanContext(context).execution_id
        user_task = EvaluationPlanContext(context).user_task
        evaluated_steps = EvaluationPlanContext(context).evaluated_steps
        results_steps = EvaluationPlanContext(context).resultsaechstep
        plan = EvaluationPlanContext(context).plan
        
        evaluated_steps_json = [
            evaluated_step.model_dump_json()
            for evaluated_step in evaluated_steps
        ]
        results_steps_json = [
            result_step.model_dump_json()
            for result_step in results_steps
        ]
        
        return f"""
                Виконання завдання {execution_id}. Оціни завершений план та надай оцінку його виконання.
                Ось оцінюваний план: {plan.model_dump_json()}. Чи він повністю відповідає поставленій цілі завдання.
                Завдання користувача, для якого розроблений був даний план: {user_task}.
                Виконання плану відбувалося покроково. На кожному кроці отримувався результат.
                Результати виконання по крокам: {json.dump(results_steps_json)}.
                Кожен результат кроку оцінювався. Оцінки кожного кроку плану: {json.dump(evaluated_steps_json)}.
                """
    