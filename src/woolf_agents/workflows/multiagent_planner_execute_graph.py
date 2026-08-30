import logging

from langgraph.graph import START, END
from langgraph.types import interrupt
from src.woolf_agents.core.decorators.logging_node import (
                                                          logging_node,
                                                          require_state
                                                          )
from typing import TypeVar, Generic, Any

from src.woolf_agents.workflows.tool_calling_worker import ToolCallingWorker
from .base_graph import BaseGraph
from .nodes import GraphNode
from .edges import GraphEdge, ConditionalGraphEdge
from .state import PlanExecuteState, PlanExecuteStatus, SourceInterrupt
from langchain_core.messages import HumanMessage
from src.woolf_agents.domains.artifacts.schemas.base import (
                                BaseTaskPlan, 
                                BasePlanStep, 
                                BaseStepResult, 
                                StepEvaluation,
                                PlanEvaluation,
                                PlanDecisionStatus,
                                StepDecision)
from src.woolf_agents.domains.artifacts.schemas.contracts import FinalResponseContext, HistoricalResearchExecutionResult, HistoricalResearchStepResult, HypothesisEvaluationStep, PlanStepStatus, StepExecutionContext, StepEvaluationContext, EvaluationPlanContext
from .agent_worker import AbstractAgentWorker, AgentWorker
import json


logger = logging.Logger(__name__)

StateT = TypeVar("StateT")
OutputT = TypeVar("OutputT")

class MultiAgentPlannerExecuteGraph(
    BaseGraph[StateT],
    Generic[StateT, OutputT]
    ):
    
    EXECUTENODE="executer_node"
    REPLANNODE="replanner_node"
    PLANNODE="plan_node"
    COUNTERNODE="counter_node"
    
    def __init__(self,
                 state_schema, 
                 model, 
                 tools, 
                 output_schema, 
                 system_prompt, 
                 executor, 
                 stop_controller, 
                 checkpointer,
                 workers: dict,
                 plan_schema: BaseTaskPlan):
        super().__init__(
            state_schema, 
            model, 
            tools, 
            output_schema, 
            system_prompt, 
            executor, 
            stop_controller, 
            checkpointer)
        self._workers = workers
        self._llm_plan_structured_output = self._model.with_structured_output(plan_schema)
    
    @logging_node("_plan_node")
    @require_state("messages", "user_task")
    async def _plan_node(self, state: StateT)->dict[str, Any]:
                
        logger.info(f"Початок планування")
      
        plan = (    
                await self._executor.model_invoke(
                self._llm_plan_structured_output,
                    [      
                        self._system_message,
                        HumanMessage(
                                content=f"""
                                    Тобі доступне завдання користувача.
                                    Зроби чіткий план для виконання завдання.
                                    Завдання користувача: {state.get("user_task")} 
                                    - сформуй лише план;
                                    - не виконуй кроки;
                                    - не вигадуй operations поза schema;
                                    - використовуй лише необхідні operations;
                                    - не додавай кроки тільки заради використання всіх доступних operations.
                                    - формуй план з 4-7 кроків;
                                    - не пояснюй свої міркування;
                                    - не повторюй завдання;
                                    - поверни лише структурований план;
                                    - якщо operation = "retrieve_sources", то research_query має містити пошуковий запит;
                                    для кожної іншої операції research_query має бути null;
                                    - ніколи не генеруй research_query для: extract_claims, generate_hypotheses, evaluate_hypotheses, synthesize_conclusion; 
                                    Правила: Правила формування кроків плану:

                                    1. Якщо для виконання кроку потрібно отримати нові дані із зовнішнього
                                    або внутрішнього джерела через інструмент, встанови:
                                    require_tools = true

                                    2. До таких кроків належать:
                                    - пошук історичних джерел;
                                    - retrieval з векторної БД;
                                    - пошук пов'язаних джерел;
                                    - отримання сусідніх chunks;
                                    - web search;
                                    - будь-який інший виклик tool.

                                    3. require_tools = false допустимо лише тоді, коли крок може бути виконаний
                                    без виклику інструментів на основі вже наявного контексту та результатів.

                                    4. require_reasoning = true встановлюй лише тоді, коли крок потребує
                                    окремого аналітичного/логічного опрацювання вже отриманої інформації.

                                    5. require_tools і require_reasoning не можуть одночасно бути true.

                                    6. Крок "знайти / отримати / retrieve / search джерела" ОБОВ'ЯЗКОВО:
                                    require_tools = true
                                    require_reasoning = false

                                    """
                                    
                            )   
                        ]
                    )
                )
        #if plan["parsed"] is None:
        #    logger.error(
        #        "Invalid planner output: %s",
        #        plan["raw"].content,
        #    )
        
        #raise plan["parsing_error"]
        
        #plan = response["parsed"]
                    
               
        logger.info(f"План сформовано {len(plan.steps)}")
        return {
                    "plan": plan,
                    "step_count": 1,
                    "len_steps": len(plan.steps),
                    "execution_status": PlanExecuteStatus.RUNNING,
                    "step_status": PlanStepStatus.PENDING
                }
    
    @logging_node("_executor_node")
    @require_state("messages", "plan", "current_step_idx", "execution_status")
    async def _executor_node(self, state: StateT)->dict[str, Any]:
        """Виконує кроки плана, сформованого у вузлі PLANNNODE та у вузлі REPLANNER"""
        logger.info("Виконуємо вузол EXECUTOR")
        current_step_idx:int = PlanExecuteState(state).get("current_step_idx")
        current_step:HypothesisEvaluationStep = PlanExecuteState(state).get("plan").steps[current_step_idx]
        previous_results: list[HistoricalResearchStepResult] = PlanExecuteState(state).get("results")
        user_task = PlanExecuteState(state).get("user_task")
        execution_id = PlanExecuteState(state).get("execution_id")
        execution_status: PlanExecuteStatus = PlanExecuteState(state).get("execution_status")
        evaluated_steps: list[StepEvaluation] = PlanExecuteState(state).get("evaluated_steps")
        step_status = current_step.step_status
        plan = PlanExecuteState(state).get("plan")
        human_decision = PlanExecuteState(state).get("human_decision")
        interrupt_reason = PlanExecuteState(state).get("interrupt_reason")
        source_interrupt: SourceInterrupt = PlanExecuteState(state).get("source_interrupt")
        step_id = current_step.id
        response=None
        plan_evaluation=None
        step_evaluation=None
        
        if source_interrupt != SourceInterrupt.NO_SOURCE:
            response=PlanExecuteState(state).get("current_step_result")
            if source_interrupt == SourceInterrupt.EVALUATION_PLAN:
                execution_status = PlanExecuteStatus.READY_FOR_PLAN_EVALUATION
            if source_interrupt == SourceInterrupt.EVALUATION_STEP:
                execution_status = PlanExecuteStatus.RUNNING
       
        if execution_status == PlanExecuteStatus.RUNNING:  
            if source_interrupt == SourceInterrupt.NO_SOURCE:
                context = StepExecutionContext(
                                        user_task=user_task,
                                        current_step=current_step,
                                        previous_results=previous_results,
                                        execution_id=execution_id,
                                        step_status=step_status,
                                        step_id=step_id
                                    )
                if current_step.require_tools:
                        response = await self._workers["tool_worker"].execute(
                            context=context
                        )
                if current_step.require_reasoning:
                        response = await self._workers["reasoning_worker"].execute(
                            context=context
                        )
            
            step_evaluation_context = StepEvaluationContext(
                                execution_id=execution_id,
                                user_task=user_task,
                                current_step=current_step,
                                current_step_result=response,
                                human_decision=human_decision,
                                interrupt_reason=interrupt_reason
                            )
                
            step_evaluation: StepEvaluation = await self._workers["step_evaluating_worker"].execute(
                                context=step_evaluation_context
                            )
            match step_evaluation.decision:
                    case StepDecision.REPLAN:
                        execution_status = PlanExecuteStatus.REPLANNING
                    case StepDecision.INTERRUPT:
                        execution_status = PlanExecuteStatus.WAITTING_FOR_HUMAN
                    case StepDecision.CONTINUE:
                        execution_status == PlanExecuteStatus.RUNNING
            if execution_status == PlanExecuteStatus.WAITTING_FOR_HUMAN:
                    source_interrupt = SourceInterrupt.EVALUATION_STEP 
                    interrupt_reason = step_evaluation.reason
            else:
                    source_interrupt = SourceInterrupt.NO_SOURCE
                    interrupt_reason = None
                
        if execution_status == PlanExecuteStatus.READY_FOR_PLAN_EVALUATION:
              
                plan_evaluation_context = EvaluationPlanContext(
                    execution_id=execution_id,
                    user_task=user_task,
                    evaluated_steps=evaluated_steps,
                    resultsaechstep=previous_results,
                    plan=plan,
                    human_decision=human_decision,
                    interrupt_reason=interrupt_reason
                )
                
                plan_evaluation:PlanEvaluation = await self._workers["evaluating_worker"].execute(
                            context=plan_evaluation_context
                        )
                match plan_evaluation.decision:
                    case PlanDecisionStatus.COMPLETE:
                                execution_status = PlanExecuteStatus.COMPLETED
                    case PlanDecisionStatus.FAIL:
                                execution_status = PlanExecuteStatus.FAILED
                    case PlanDecisionStatus.REPLAN:
                                execution_status = PlanExecuteStatus.REPLANNING
                    case PlanDecisionStatus.INTERRUPT:
                                execution_status = PlanExecuteStatus.WAITTING_FOR_HUMAN
                if execution_status == PlanExecuteStatus.WAITTING_FOR_HUMAN:
                     source_interrupt = SourceInterrupt.EVALUATION_PLAN 
                     interrupt_reason = PlanEvaluation.reason
                else:
                     source_interrupt = SourceInterrupt.NO_SOURCE
                     interrupt_reason = None
            
        
        return {
            "human_decision": None,
            "source_interrupt": source_interrupt,
            "current_step_result": response,
            "results": [response] if response is not None else [],
            "step_count": 1,
            "evaluated_current_step":step_evaluation,
            "plan_execution_evaluated": plan_evaluation,
            "execution_status": execution_status,
            "evaluated_steps": [step_evaluation] if step_evaluation is not None else [],
            "interrupt_reason": interrupt_reason
        }
        
    def _counter_node(self, state: StateT) ->dict[str, Any]:
        """Обчислює лічильник поточного кроку"""
        logger.info("Запускається вузол лічильника")
        execution_status:PlanExecuteStatus = PlanExecuteState(state).get("execution_status")
        len_steps = PlanExecuteState(state).get("len_steps")
        current_step_idx = PlanExecuteState(state).get("current_step_idx")
        
        if (execution_status != PlanExecuteStatus.COMPLETED and 
                        execution_status != PlanExecuteStatus.FAILED and
                             execution_status != PlanExecuteStatus.REPLANNING):
            if current_step_idx > len_steps - 1:
                execution_status = PlanExecuteStatus.FAILED
                raise ValueError(f"Індекс кроку {current_step_idx} поза межами кількості кроків плану {len_steps}")
            
            if current_step_idx == len_steps - 1:
                execution_status = PlanExecuteStatus.READY_FOR_PLAN_EVALUATION
            
        
        return {
            "execution_status": execution_status,
            "step_count": 1,
            "current_step_idx": 1 if execution_status == PlanExecuteStatus.RUNNING else 0
        }
    
    
    @logging_node("_replanner_node")
    @require_state(
        "messages", 
        "plan", 
        "user_task", 
        "evaluated_steps", 
        "results", 
        "plan_execution_evaluated",
        "current_step_idx"
        )
    async def _replanner_node(self, state: StateT) -> dict[str, Any]:
        """Виконує перепланування плану, який визначено до перепланування"""
        logger.info("Виконуємо перепланування початкового плану")
        plan = PlanExecuteState(state).get("plan")
        user_task = PlanExecuteState(state).get("user_task")
        steps_evals_current_plan = PlanExecuteState(state).get("evaluated_steps")
        steps_results = PlanExecuteState(state).get("results")
        plan_evaluated = PlanExecuteState(state).get("plan_execution_evaluated") 
        current_step_idx = PlanExecuteState(state).get("current_step_idx")
        evaluated_steps_json = [
            evl_step.model_dump_json() 
            for evl_step in steps_evals_current_plan
        ]
        results_steps_json = [
            res_step.model_dump_json() 
            for res_step in steps_results
        ]
        
        
        if plan_evaluated is not None:
             content = f"""
                        Переплануй поточний план. Ось сам план {plan.model_dump_json()}. Цей план невдалий, визначено на перепланування при оцінці плану цілком.
                        Початкове завдання користувача: {user_task}. 
                        Оцінки виконання поточного плану на кожному з кроків: {json.dumps(evaluated_steps_json)}.
                        Отримані результати на кожному з кроків {json.dumps(results_steps_json, ensure_ascii=False, indent=2)}.
                        Оцінка повного плану {plan_evaluated.model_dump_json()}.
                    """
        else: 
             content = f"""
                        Переплануй поточний план на основі невдалого плана. Оціни які кроки були успішними, а які невдалими.
                        Ось сам план {plan.model_dump_json()}. Цей план невдалий, визначено на перепланування при оцінці плану
                        на поточному кроці {current_step_idx}.
                        Початкове завдання користувача: {user_task}. 
                        Оцінки виконання поточного плану на кожному з кроків: {json.dumps(evaluated_steps_json)}.
                        Отримані результати на кожному з кроків {json.dumps(results_steps_json, ensure_ascii=False, indent=2)}.
                    """
            
        
        new_plan = await self._executor.model_invoke(
                    self._llm_plan_structured_output,
                    [
                          self._system_message,
                          HumanMessage(
                              content=content
                          )
                    ]
                      
            )
    
        
        return {
            "plan": new_plan,
            "revised_plan": [plan],
            "current_step_idx": -current_step_idx,
            "execution_status": PlanExecuteStatus.RUNNING
        }
    
    def _stoped_node(self, state: StateT) ->dict[str, Any]:
        """Завершує виконання через внутрішню помилку faile"""
        return {
            "execution_status": PlanExecuteStatus.FAILED
        }
    
    @logging_node("_interrupt_node")
    @require_state("messages", "step_count")
    async def _interrupt_node(self, state: StateT) -> dict[str, Any]:
        """Запит на дію/approve людини"""
        logger.info("Виконуємо вузол, що очікує дію-підтеврдження людини")
        execution_id = PlanExecuteState(state).get("execution_id")
        interrupt_reason = PlanExecuteState(state).get("interrupt_reason")
         
        human_decision = interrupt(
            {
                "execution_id": execution_id,
                "interrupt_reason": interrupt_reason,
                "allowed_actions": [
                    "continue",
                    "approve",
                    "cancel"
                ]
            }
        )
        return {
            "human_decision": human_decision,
            "step_count": 1
        }
        
         
    
    @logging_node("_structured_ouput_node")
    @require_state("messages")
    async def _structured_output_node(self, state: StateT) ->dict[str, Any]:
        """"Повертає структуровану відповідь"""
        logger.info("Виконує формування фінальної відповіді для користувача")
        
        user_task = PlanExecuteState(state).get("user_task")
        plan_evaluation = PlanExecuteState(state).get("plan_execution_evaluated")
        final_plan = PlanExecuteState(state).get("plan")
        step_results = PlanExecuteState(state).get("results")
        execution_id = PlanExecuteState(state).get("execution_id")
        context = FinalResponseContext(
            user_task=user_task,
            plan_evaluation=plan_evaluation,
            final_plan=final_plan,
            step_results=step_results,
            execution_id=execution_id
        )
        response: HistoricalResearchExecutionResult = await self._workers["structured_output_worker"].execute(context=context)
        
        return {
            "structured_response": response,
            "step_count": 1
        }
    
    def _router_after_execute(self, state: StateT) -> dict[str, Any]:
        """Роутер - вирішує куди направити workflow: перепланування, подальше виконання чи 
        завершення виконання плану та формування завершенної відповіді"""
        logger.info("Виконуємо роутер")
        execution_status = PlanExecuteState(state).get("execution_status")
        if execution_status == PlanExecuteStatus.REPLANNING:
           return self.REPLANNODE
        if (execution_status == PlanExecuteStatus.READY_FOR_PLAN_EVALUATION 
            or execution_status ==PlanExecuteStatus.RUNNING):
            return self.EXECUTENODE
        if execution_status == PlanExecuteStatus.COMPLETED:
            return self.STRUCTURED_OUTPUT_NODE
        if execution_status == PlanExecuteStatus.FAILED:
            return self.STOPPED_NODE
        if execution_status == PlanExecuteStatus.WAITTING_FOR_HUMAN:
            return self.INTERRUPT_NODE
        
        raise ValueError(
        f"Непідтримуваний execution_status у "
        f"_router_after_execute: {execution_status}"
    )
    
    
    def _create_conditional_edges(self) -> tuple[ConditionalGraphEdge[StateT], ...]:
         return (
              ConditionalGraphEdge(
                  first_node=self.COUNTERNODE,
                  router=self._router_after_execute,
                  routes={
                      self.EXECUTENODE: self.EXECUTENODE,
                      self.REPLANNODE: self.REPLANNODE,
                      self.STRUCTURED_OUTPUT_NODE: self.STRUCTURED_OUTPUT_NODE,
                      self.STOPPED_NODE:self.STOPPED_NODE,
                      self.INTERRUPT_NODE:self.INTERRUPT_NODE
                  }
              ),
         ) 
    
    def _create_edges(self) ->tuple[GraphEdge, ...]:
         return (
             GraphEdge(
                 first_node=START,
                 second_node=self.PLANNODE
             ),
             GraphEdge(
                 first_node=self.PLANNODE,
                 second_node=self.EXECUTENODE
             ),
             GraphEdge(
                first_node=self.EXECUTENODE,
                second_node=self.COUNTERNODE  
             ),
             GraphEdge(
                 first_node=self.REPLANNODE,
                 second_node=self.EXECUTENODE
             ),
             GraphEdge(
                 first_node=self.STRUCTURED_OUTPUT_NODE,
                 second_node=END
             ),
             GraphEdge(
                 first_node=self.INTERRUPT_NODE,
                 second_node=self.EXECUTENODE
             )
         )         
    
    def _create_nodes(self) -> tuple[GraphNode[StateT],...]:
        return (
            GraphNode(
                name_node=self.PLANNODE,
                func=self._plan_node
            ),
            GraphNode(
                name_node=self.EXECUTENODE,
                func=self._executor_node
            ),
            GraphNode(
                name_node=self.COUNTERNODE,
                func=self._counter_node
            ),
            GraphNode(
                name_node=self.REPLANNODE,
                func=self._replanner_node
            ),
            GraphNode(
                name_node=self.STRUCTURED_OUTPUT_NODE,
                func=self._structured_output_node
            ),
            GraphNode(
                name_node=self.STOPPED_NODE,
                func=self._stoped_node
            ),
            GraphNode(
                name_node=self.INTERRUPT_NODE,
                func=self._interrupt_node
            )
        )
    
    