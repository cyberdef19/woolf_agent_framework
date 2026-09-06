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
        current_step = context.current_step
        expected_result =current_step.expected_result
        task_step = current_step.objective
        current_step_result = context.current_step_result
        task_step_result = current_step_result.summary
        execution_id = context.execution_id
        user_task = context.user_task
        
        return f"""
                  
                Виконання завдання: {execution_id}. Оціни результат кроку виконання плану.
                Завдання кроку: {task_step}.
                Отриманий результат виконання кроку: {task_step_result}.
                Очікуваний результат виконання кроку: {expected_result}.
                Завдання користувача: {user_task}
                
                Сформуй коректний структурований результат відповідно до заданої схеми.
                Якщо відповідь містить суттєві недоліки або суттєві суперечності, тоді в тебе
                є можливість переробити план для отримання кращого результату.  
                Якщо у відповідь не може бути отримана шляхом перепланування плану, то можеш заповнити
                поле для переривання для підключення користувача.
                
                Не повертай REPLAN лише тому, що:
                - доступно мало джерел;
                - джерела неповні;
                - можна потенційно знайти додаткові джерела;
                - confidence не є високим.

                Якщо отриманих даних достатньо для формування обережного висновку
                з позначенням невизначеності, план вважається придатним до завершення.

                REPLAN дозволений лише якщо поточна структура плану принципово
                не дозволяє відповісти на дослідницьке питання. 
                                
                """
       
        
        
        
        