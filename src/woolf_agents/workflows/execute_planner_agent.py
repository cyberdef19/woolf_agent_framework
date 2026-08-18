import logging
import json
from langgraph.graph import StateGraph, START, END
from langchain_core.language_models.chat_models import BaseChatModel
from .base_graph import BaseGraph
from .nodes import GraphNode
from .edges import GraphEdge, ConditionalGraphEdge
from .state import PlanExecuteState
from typing import TypeVar, Generic, Any
from src.woolf_agents.runtime.stop_controller import StopController
from src.woolf_agents.llm.executor import LLMExecutor
from collections.abc import Sequence
from langgraph.types import interrupt
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, AIMessage
from src.woolf_agents.domains.artifacts.schemas.base import BaseTaskPlan, BasePlanStep, BaseStepResult, StepEvaluation, PlanEvaluation, PlanDecisionStatus
from src.woolf_agents.domains.artifacts.schemas.contracts import HistoricalResearchStepResult, StepExecutionContext
from src.woolf_agents.core.result import ExecutionStatus
from langgraph.checkpoint.base import BaseCheckpointSaver

StateT = TypeVar("StateT")
OutputT = TypeVar("OutputT")

logger = logging.Logger(__name__)

class ExecutePlannerAgent(
    BaseGraph[StateT],
    Generic[StateT, OutputT]):
    
    PLANNER="planner_node"
    EXECUTOR="executor_node"
    REPLANNER="replanner_node"
    COMPLETE_STEP_NODE="complete_step_node"
    STEPEVALUATOR = "step_evaluator_node"
    EVALUATOR = "evaluator_node"
    INTERRUPT = "interrupt_node"
    PUSHSTEP = "push_step_node"
    PREPARESTEP = "prepare_step_node"
    
    
    def __init__(self,
                 state_schema: type[StateT],
                 model: BaseChatModel,
                 output_schema: type[OutputT],
                 plan_schema: BaseTaskPlan,
                 step_evaluate_schema: StepEvaluation, 
                 plan_evaluation: PlanEvaluation,
                 tools: Sequence[BaseTool],
                 system_prompt: str,
                 stop_controller: StopController,
                 executor: LLMExecutor,
                 checkpointer: BaseCheckpointSaver
                 ):
        super().__init__(
            state_schema=state_schema,
            model=model,
            output_schema=output_schema,
            tools=tools,
            system_prompt=system_prompt,
            stop_controller=stop_controller,
            executor=executor,
            checkpointer=checkpointer
            )
        self._plan_schema = plan_schema
        self._llm_plan_structured_output = model.with_structured_output(plan_schema)
        self._llm_step_evaluate_structured_output = model.with_structured_output(step_evaluate_schema)
        self._llm_evaluated_structured_output = model.with_structured_output(plan_evaluation)
        #self._SYSTEM_EXECUTOR_MESSAGE = ""
        
    async def _planner_node(self, state: StateT) ->dict[str, Any]:
        """Вузол графа планує виконання завдання користувача"""
        
        if "messages" not in state:
            raise ValueError("Відсутні необхідні поля у стані для створення плану")
        
        logger.info(f"Початок планування {state["execution_id"]}")
        # Тимчасова діагностика Pydantic schema
        #schema = self._plan_schema.model_json_schema()

        """print(
            json.dumps(
                schema,
                indent=2,
                ensure_ascii=False,
            )
        )"""

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
                            Якщо operation == "retrieve_sources": дозволено викликати retrieval tool.

                            Для інших operations:
                                використовуй результати попередніх кроків.
                                Не виконуй повторний retrieval, якщо поточний план
                                явно не містить нового retrieve_sources step.
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
            "execution_status": ExecutionStatus.PARTIAL
        }
        
    async def _prepare_step_node(self, state: StateT)->dict[str, Any]:
        """Готує контекст для виконання кроку"""
        if "messages" not in state:
            raise ValueError("Відсутні необхідні поля у стані для створення плану")
        context_step = PlanExecuteState(state).get("context_step")
        current_step_idx = PlanExecuteState(state).get("current_step_idx")
        context_step: StepExecutionContext = StepExecutionContext(
             user_task=PlanExecuteState(state).get("user_task"),
             current_step=PlanExecuteState(state).get("plan").steps[current_step_idx],
             previous_results=PlanExecuteState(state).get("results", [])
        )    
        step_messages_start_idx = state["step_messages_start_idx"]
        return {
            "context_step": context_step,  
            "step_messages_start_idx": step_messages_start_idx  
        }
        
        
        
    async def _execute_node(self, state:StateT) -> dict[str, Any]:
        """Вузол виконує отриманий план крок за кроком"""
        if "messages" not in state:
            raise ValueError("Відсутні необхідні поля у стані для створення плану")
        cur_idx:int = PlanExecuteState(state).get("current_step_idx")
        if cur_idx >= PlanExecuteState(state).get("len_steps"):
            raise RuntimeError("Запит на виконання кроку плану після плану")
        
        step = PlanExecuteState(state).get("plan").steps[cur_idx]
        logger.info(f"Виконання кроку плана: {cur_idx} - {step.objective}")
        step_messages_start_idx = state["step_messages_start_idx"]
        current_step_messages = state["messages"][step_messages_start_idx:]
    
        
        response = await self._executor.model_invoke(
            self._tool_model,
            [
                self._system_message,
                *current_step_messages,
                HumanMessage(
                    content=f"""
                    Притримуючись плану,
                    виконай поточний крок за наданим контекстом.
                    {state["context_step"].model_dump_json(indent=2)}
                    """
                )
            ]
        )  
        logger.info(f"Завершили роботу з виконання кроку {cur_idx}")
         
        return {
            "executor_response": response,
            "messages": [response],
            "step_count": 1,
            "step_started": True
        }
    
    def _router_before_evaluator(self, state: StateT)->str:
        """Визначає продовження кроку: чи наступним виклик інструментів чи маємо якусь неоцінену відповідь"""
        logger.info("Виконання вузла роутера before evaluator")
        if "messages" not in PlanExecuteState(state):
             raise ValueError("Відсутні необхідні поля у стані для створення плану")
        executor_response = PlanExecuteState(state).get("executor_response")
        if not isinstance(executor_response, AIMessage):
            raise TypeError("Очікується AIMessage")
        tool_calls = executor_response.tool_calls
        
        if len(tool_calls) == 0:
            logger.info("Йдемо на вузол COMPLETE_STEP_NODE")
            return self.COMPLETE_STEP_NODE
        else:
            logger.info("Йдемо на вузол TOOL_NODE")
            return self.TOOLS_NODE
        
    async def _complete_step_node(self, state: StateT) ->dict[str, Any]:
        """Визначає завершений крок плану"""
        logger.info("Виконання вузла complete_step_node")
        if "messages" not in PlanExecuteState(state):
            raise ValueError("Відсутні необхідні поля у стані для створення плану")
        cur_idx = PlanExecuteState(state).get("current_step_idx")
        step = PlanExecuteState(state).get("plan").steps[cur_idx]
        step_result = BaseStepResult(
            summary=PlanExecuteState(state)["messages"][-1].content,
            step_id=step.id
            )
        return  {
            "current_step_result": step_result,
            "step_count": 1
        }
    
    async def _step_evaluator_node(self, state: StateT) -> dict[str, Any]:
        """Оцінює адекватність отриманих результатів після виконання кроку плана"""
        logger.info("Виконання взула оцінки конкретного кроку")
        if "messages" not in PlanExecuteState(state):
            raise ValueError("Відсутні необхідні поля у стані для створення плану")
        
        current_step = PlanExecuteState(state).get("current_step_idx")
        current_step_result = PlanExecuteState(state).get("current_step_result")
        
        response = await self._executor.model_invoke(
            self._llm_step_evaluate_structured_output,
            [
                self._system_message,
                HumanMessage(
                    
                    content=f"""
                            Для кроку плану: {current_step}
                            Проведи оцінку результата: {current_step_result.model_dump_json(indent=2)}
                            """,
                    
                )
            ]
        )
        return {
            "step_count": 1,
            "evaluated_current_step": response
        }
        
    def _router_after_evaluator_step(self, state: StateT)->dict[str, Any]:
        """Визначає подальший потік виконання: перепланування, продовження плану, оцінка плану цілком, якщо останній крок"""
        logger.info("Виконується роутер after evaluate step")
        if "messages" not in PlanExecuteState(state):
            raise ValueError("Відсутні необхідні поля у стані")
        eval:StepEvaluation = PlanExecuteState(state).get("evaluated_current_step")
        desicion = eval.decision
        
        match desicion:
            case "continue":
                if PlanExecuteState(state).get("current_step_idx") == PlanExecuteState(state).get("len_steps") - 1:
                    return self.EVALUATOR
                return self.PUSHSTEP
            case "replan":
                return self.REPLANNER     
            
    async def _push_step_node(self, state: StateT)->dict[str, Any]:
        """Виконує збільшення кроку після отримання оцінки кроку з рішенням continue"""
        logger.info("Виконується вузол для збільшення значення кроку")
        if "messages" not in PlanExecuteState(state):
            raise ValueError("Відсутні необхідні поля у стані")   
    
        current_step_result = PlanExecuteState(state).get("current_step_result")
        current_eval_step = PlanExecuteState(state).get("evaluated_current_step")  
         
        return {
            "current_step_idx": 1,
            "evaluated_steps": [current_eval_step],
            "results": [current_step_result],
            "step_start": False
        }
        
         
    async def _replanner_node(self, state: StateT) -> dict[str, Any]:
        """Виконує перепланування старого плану"""
        logger.info("Виконується роутер after evaluate step")
        if "messages" not in PlanExecuteState(state):
                raise ValueError("Відсутні необхідні поля у стані")
        current_plan = PlanExecuteState(state).get("plan")
        PlanExecuteState(state).update(
            {
            "history_plans": current_plan
            }
        )
        response = await self._executor.model_invoke(
             self._llm_plan_structured_output,
             [
                 self._system_message,
                 *state["messages"],
                 HumanMessage(
                     content=f"""
                     Переплануй кроки плану. Надано план, що не є валідним {current_plan.model_dump_json}
                     Цей план слід перепланувати відповідно до користувацького завдання {PlanExecuteState(state).get("user_task")}
                     """
                     
                 )
             ]
        )
    
        return {
            "plan": response,
            "len_steps": len(BaseTaskPlan(response).steps),
            "current_steps_idx": -PlanExecuteState(state).get("current_step_idx"),
            "current_step_result": None,
            "evaluated_current_step": None,
            "revised_plans": current_plan,
            "results": [],
            "executor_response": None
        }

    async def _interrupt_node(self, state: PlanExecuteState) -> dict[str, Any]:
            logger.info("Очікується втручання користувача")
            human_decision = interrupt(
                    {
                    "type": "human_approval",
                    "reason": state.get(
                        "interrupt_reason",
                        "Потрібне підтвердження користувача."
                    ),
                    "options": [
                        "continue"
                        "approve",
                        "cancel",
                    ],
                }
            )

            logger.info(
                    "Отримано рішення користувача: %s",
                    human_decision,
                    )
            return {
                "human_decision": human_decision,
                "execution_status": "partial",
            }
            
    def _route_after_interrupt(self, state: PlanExecuteState) -> str:

            decision = state["human_decision"]
            if decision == "continue":
                return self.STRUCTURED_OUTPUT_NODE
            if decision == "approve":
                return self.REPLANNER_NODE

            if decision == "cancel":
                return self.STOPPED_NODE

            raise RuntimeError(
                f"Unknown human decision: {decision}"
            )
    
    async def _evaluator_node(self, state: StateT) -> dict[str, Any]:
        """Виконує оцінку виконання плану цілком після виконання його кроків"""
        logger.info("Виконує повну оцінку виконанного завдання згідно поточного плану")
        if "messages" not in PlanExecuteState(state):
                raise ValueError("Відсутні необхідні поля у стані")  
                                                 
        current_step_result = PlanExecuteState(state).get("current_step_result")
        step_results = PlanExecuteState(state).get("results")
        step_results.append(current_step_result)
        user_task = PlanExecuteState(state).get("user_task")
        evaluated_step = PlanExecuteState(state).get("evaluated_current_step")
        evals = PlanExecuteState(state).get("evaluated_steps")
        evals.append(evaluated_step)
        plan = PlanExecuteState(state).get("plan")
        step_results_json = json.dumps(
            [
                result.model_dump_json
                for result in step_results
            ]
        )
        evals_json = json.dumps(
            [
                evl.model_dump_json
                for evl in evals
            ]
        )
        
        response = await self._executor.model_invoke(
                  self._llm_evaluated_structured_output,
                  [
                      self._system_message,
                      *state["messages"],
                      HumanMessage(
                          content=f"""
                           Надай повну завершальну оцінку виконанню плана {plan.model_dump_json}
                           За завданням користувача {user_task}. Оцінка має грунтуватися 
                           на результатах кроків {step_results_json}, а також на оцінках отриманих по крокам {evals_json}.
                           Поверни структурований об'єкт у відповідь у якості оцінки. Завершальний висновок має бути
                           відображений у полі decision типу PlanDecision.
                          """
                          
                      )
                  ]
        )
        
        return  {
            "plan_execution_evaluated": response,
            "step_count": 1,
            "results": [current_step_result],
            "evaluated_steps": [evaluated_step]
        }
    
    def _router_after_evaluated_plan(self, state: StateT)->dict[str, Any]:
        """Виконує подальшу маршрутизацію потоку виконання після повної оцінки плану"""
        logger.info("Виконує маршрутизацію потоку виконання після оцінки плану")
        if "messages" not in PlanExecuteState(state):
                raise ValueError("Відсутні необхідні поля у стані")
        plan_evaluated = PlanExecuteState(state).get("plan_execution_evaluated")
        match plan_evaluated.decision:
            case PlanDecisionStatus.COMPLETE:
                return self.STRUCTURED_OUTPUT_NODE
            case PlanDecisionStatus.REPLAN:
                return self.REPLANNER
            case PlanDecisionStatus.INTERRUPT:
                return self.INTERRUPT
            case PlanDecisionStatus.FAIL:
                return self.STOPPED_NODE
            
    async def _stopped_node(self, state: StateT)->dict[str, Any]:
        """Зазначає, що виконання плану слід зупинити. після несподіваного fail"""
        return {
            "execution_status": ExecutionStatus.STOP,
            "step_count": 1
        } 
    
    async def _structured_output_node(self, state: StateT)->dict[str, Any]:
        """Формує завершальну відповідь на завдання користувача"""
        logger.info("Виконує маршрутизацію потоку виконання після оцінки плану")
        if "messages" not in PlanExecuteState(state):
                raise ValueError("Відсутні необхідні поля у стані")
        step_results = PlanExecuteState(state).get("results")
        user_task = PlanExecuteState(state).get("user_task")  
        step_results_json = json.dumps(
                    [
                        result.model_dump_json
                        for result in step_results
                    ]
                ) 
        response = self._executor.model_invoke(
            self._llm_structured_output,
            [
                self._system_message,
                *state["messages"],
                HumanMessage(
                    content=f"""
                    Надай структурований об'єкт фіналізуючої відповіді на завдання користувача {user_task}
                    на основі отриманих результатів попередніх кроків {step_results_json}
                    """
                )
            ]
        )
        
        return {
            "structured_response": response,
            "step_count": 1,
            "execution_status": ExecutionStatus.SUCCESS
        } 
    def _create_conditional_edges(self)->tuple[ConditionalGraphEdge[StateT], ...]:
        return (
            ConditionalGraphEdge(
                first_node=self.EXECUTOR,
                router=self._router_before_evaluator,
                routes={
                    self.TOOLS_NODE: self.TOOLS_NODE,
                    self.COMPLETE_STEP_NODE: self.COMPLETE_STEP_NODE
                }
            ),
            ConditionalGraphEdge(
                first_node=self.STEPEVALUATOR,
                router=self._router_after_evaluator_step,
                routes={
                    self.REPLANNER:self.REPLANNER,
                    self.PUSHSTEP:self.PUSHSTEP,
                    self.EVALUATOR:self.EVALUATOR
                }
            ),
            ConditionalGraphEdge(
                first_node=self.EVALUATOR,
                router=self._router_after_evaluated_plan,
                routes={
                    self.STOPPED_NODE:self.STOPPED_NODE,
                    self.STRUCTURED_OUTPUT_NODE:self.STRUCTURED_OUTPUT_NODE,
                    self.REPLANNER:self.REPLANNER,
                    self.INTERRUPT:self.INTERRUPT
                }
            ),
            ConditionalGraphEdge(
                first_node=self.INTERRUPT,
                router=self._route_after_interrupt,
                routes={
                    self.STOPPED_NODE: self.STOPPED_NODE,
                    self.STRUCTURED_OUTPUT_NODE: self.STRUCTURED_OUTPUT_NODE,
                    self.REPLANNER: self.REPLANNER
                }
            )
        )
        
    
    def _create_edges(self)->tuple[GraphEdge, ...]:
        return (
            GraphEdge(
                first_node=START,
                second_node=self.PLANNER
            ),
            GraphEdge(
                first_node=self.PLANNER,
                second_node=self.PREPARESTEP
            ),
            GraphEdge(
                first_node=self.TOOLS_NODE,
                second_node=self.PREPARESTEP
            ),
            GraphEdge(
                first_node=self.PUSHSTEP,
                second_node=self.PREPARESTEP
            ),
            GraphEdge(
                first_node=self.PREPARESTEP,
                second_node=self.EXECUTOR
            ),
            GraphEdge(
                first_node=self.COMPLETE_STEP_NODE,
                second_node=self.STEPEVALUATOR
            ),
            GraphEdge(
                first_node=self.STRUCTURED_OUTPUT_NODE,
                second_node=END
            )
        ) 
    def _create_nodes(self)-> tuple[GraphNode[StateT],...]:
        return (
            GraphNode(
              name_node=self.PUSHSTEP,
              func=self._push_step_node  
            ),
            GraphNode(
                name_node=self.PLANNER,
                func= self._planner_node
            ),
            GraphNode(
                name_node=self.EXECUTOR,
                func=self._execute_node
            ),
            GraphNode(
                name_node=self.TOOLS_NODE,
                func=self._tool_node
            ),
            GraphNode(
                name_node=self.COMPLETE_STEP_NODE,
                func=self._complete_step_node
            ),
            GraphNode(
                name_node=self.STEPEVALUATOR,
                func=self._step_evaluator_node
            ),
            GraphNode(
                name_node=self.REPLANNER,
                func=self._replanner_node
            ),
            GraphNode(
                name_node=self.EVALUATOR,
                func=self._evaluator_node
            ),
            GraphNode(
                name_node=self.STOPPED_NODE,
                func=self._stopped_node
            ),
            GraphNode(
                name_node=self.STRUCTURED_OUTPUT_NODE,
                func=self._structured_output_node
            ),
            GraphNode(
                name_node=self.INTERRUPT,
                func=self._interrupt_node
            ),
            GraphNode(
                name_node=self.PREPARESTEP,
                func=self._prepare_step_node
            )
            
        )
    
        