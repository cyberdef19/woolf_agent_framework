import logging

from src.woolf_agents.core.decorators.logging_node import (
                                                          logging_node,
                                                          require_state
                                                          )
from typing import TypeVar, Generic, Any
from .base_graph import BaseGraph
from .nodes import GraphNode
from .state import PlanExecuteState
from langchain_core.messages import HumanMessage
from src.woolf_agents.domains.artifacts.schemas.base import BaseTaskPlan, BasePlanStep, BaseStepResult

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
    
    def __init__(self,
                 state_schema, 
                 model, 
                 tools, 
                 output_schema, 
                 system_prompt, 
                 executor, 
                 stop_controller, 
                 checkpointer):
        super().__init__(
            state_schema, 
            model, 
            tools, 
            output_schema, 
            system_prompt, 
            executor, 
            stop_controller, 
            checkpointer)
    
    @logging_node("_plan_node")
    @require_state("messages", "user_task")
    async def _plan_node(self, state: StateT)->dict[str, Any]:
                
        logger.info(f"Початок планування")
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
                    "len_steps": len(plan.steps)
                }
    
    @logging_node("_executor_node")
    @require_state("messages", "plan", "len_steps", "current_step_idx")
    async def _executor_node(self, state: StateT)->dict[str, Any]:
        """Виконує кроки плана, сформованого у вузлі PLANNNODE та у вузлі REPLANNER"""
        logger.info("Виконуємо вузол EXECUTOR")
        current_step_idx:int = PlanExecuteState(state).get("current_step_idx")
        current_step:BasePlanStep = PlanExecuteState(state).get("plan").steps[current_step_idx]
        if current_step.require_tools:
            pass
        if current_step.require_reasoning:
            pass
        if current_step.require_evaluation:
            pass
        
        return {
            "current_step_result": response,
            "results": response,
            "messages": [response],
            "step_count": 1
        }
        
    
    def _create_nodes(self) -> tuple[GraphNode[StateT],...]:
        return (
            GraphNode(
                name_node=self.PLANNODE,
                func=self._plan_node
            ),
            GraphNode(
                name_node=self.EXECUTENODE,
            )
        )
    
    