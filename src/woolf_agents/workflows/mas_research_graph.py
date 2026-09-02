
from uuid import uuid4
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph
from langgraph.types import Command, interrupt
from src.woolf_agents.core.agent_spec import AgentSpec
from src.woolf_agents.core.mcp.server import BaseFastMCP
from src.woolf_agents.core.retry import RetryPolicyAgent, RetrySettings
from src.woolf_agents.domains.artifacts.schemas.base import PlanEvaluation, PlanStepStatus, StepEvaluation
from src.woolf_agents.domains.artifacts.schemas.contracts import CriticDecision, HistoricalHypothesisEvaluationPlan, HistoricalResearchExecutionResult, HistoricalResearchStepResult, HumanReviewDecision
from src.woolf_agents.llm.config import ConfigModelAPI, LLMModel, LLMProvider, LLMSettings
from src.woolf_agents.llm.executor import LLMExecutor
from src.woolf_agents.llm.factory import LLMFactory
from src.woolf_agents.runtime.runner import AgentGraphRunner
from src.woolf_agents.runtime.settings import AgentRuntimeSettings
from src.woolf_agents.runtime.stop_controller import StopController
from src.woolf_agents.runtime.trajectory_logger import TrajectoryLogger
from src.woolf_agents.workflows.critical_agent import CriticalAgent
from src.woolf_agents.workflows.historical_superviser import HistoricalSuperviser
from src.woolf_agents.workflows.multiagent_planner_execute_graph import MultiAgentPlannerExecuteGraph
from typing import Generic, Literal, TypeVar
from langgraph.checkpoint.base import BaseCheckpointSaver
from src.woolf_agents.llm.config import url_modelrouter

from src.woolf_agents.workflows.plan_evaluator_worker import PlanEvaluatorWorker
from src.woolf_agents.workflows.prompts import system_prompts
from src.woolf_agents.workflows.reasoning_worker import ReasoningWorker
from src.woolf_agents.workflows.state import PlanExecuteState, SourceInterrupt, ToolGraphState
from src.woolf_agents.workflows.step_evaluator_worker import StepEvaluatorWorker
from src.woolf_agents.workflows.structured_output_result_worker import StructuredOutputResultWorker
from src.woolf_agents.workflows.tool_calling_worker import ToolCallingWorker
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import START

"Яке походження назви Хаджибей? Визнач представлені в доступних джерелах гіпотези та оціни, яка з них має найкращу доказову підтримку."

StateT = TypeVar("StateT")

class MASResearchGraph(Generic[StateT]):
    
    def __init__(self, 
                 state_schema: type[StateT],
                 llm: BaseChatModel,
                 checkpointer: BaseCheckpointSaver,
                 executor: LLMExecutor,
                 mcp_client: MultiServerMCPClient,
                 retry_policy: RetryPolicyAgent
                 ):
        
        self._user_task: str| None = None
        self._checkpointer = checkpointer
        self._state_schema = state_schema
        self._executor = executor
        self._workers = {}        
        self._mcp_client = mcp_client
        self._tools = []
        self._user_task = user_task
        self._llm_settings = self._get_llm_settings()
        self._llm = llm
        self._retry_policy = retry_policy
        self._plan_executor_runner: AgentGraphRunner| None = None

        self._critical_agent: CriticalAgent = self._create_critical_agent()
        self._superviser: HistoricalSuperviser = self._create_historical_superviser()
        self._graph = self._build()
        self._runner = self._create_agent_runner(self._graph)
       
        
    def _create_critical_agent(self):
        return CriticalAgent(
            model=self._llm,
            executor=self._executor,
            output_schema=CriticDecision,
            system_prompt=system_prompts["critical_system_prompt"].system_prompt
        )
    
    def _create_historical_superviser(self):
        return HistoricalSuperviser()
    
    async def _get_tools(self) ->list:
        self._tools = await self._mcp_client.get_tools()
    
    def _get_workers(self) -> dict:

        self._workers =  {
                "tool_worker": ToolCallingWorker(
                    state=ToolGraphState,
                    llm=self._llm,
                    output_schema=HistoricalResearchStepResult,
                    system_prompt=system_prompts["historical_tool_calling_spec"].system_prompt,
                    executor=self._executor,
                    stop_controller=StopController(),
                    checkpointer=self._checkpointer,
                    tools=self._tools
                ),
                "reasoning_worker":ReasoningWorker(
                    model=self._llm,
                    output_schema=HistoricalResearchStepResult,
                    executor=self._executor,
                    system_message=system_prompts["historical_reasoning_spec"].system_prompt
                    ),
                "step_evaluating_worker": StepEvaluatorWorker(
                    model=self._llm,
                    executor=self._executor,
                    system_message=system_prompts["historical_step_evaluator_spec"].system_prompt,
                    output_schema=StepEvaluation
                    ),
                "evaluating_worker": PlanEvaluatorWorker(
                    model=self._llm,
                    executor=self._executor,
                    system_message=system_prompts["historical_plan_evaluator_spec"].system_prompt,
                    output_schema=PlanEvaluation
                ),
                "structured_output_worker": StructuredOutputResultWorker(
                    model=self._llm,
                    executor=self._executor,
                    system_message=system_prompts["historical_final_responce_spec"].system_prompt,
                    output_schema=HistoricalResearchExecutionResult
                )
            }
    async def _initialize(self) -> None:
            await self._get_tools()
            self._get_workers()
            plan_executor_compiled_graph: MultiAgentPlannerExecuteGraph = self._create_plan_executor_graph() 
            self._plan_executor_runner = self._create_agent_runner(plan_executor_compiled_graph)
    
    async def _run_plan_executor(self, state: StateT) -> Command[Literal["superviser"]]:
            """Виконує планувальника задля отримання відповіді на завдання користувача """
            if self._plan_executor_runner is None:
                await self._initialize()
                
            thread_id = str(uuid4())
            result = await self._plan_executor_runner.run(
                        initial_state=self._get_initial_planer_state(self._user_task),
                        thread_id=thread_id
                        )
            return Command(
                update={
                    "research_result": result
                    },
                goto="superviser"
            )
            
    """def _get_llm_settings(self, 
                           provider = LLMProvider.OPENROUTER,
                           model = LLMModel.GPTOMINI4O,
                           base_url = url_modelrouter["openrouter_url"],
                           api_key = ConfigModelAPI.OPENROUTERKEY
                           ) -> LLMSettings: 
        return LLMSettings(
            provider=provider,
            model = model,
            base_url=base_url,
            api_key = api_key
        )"""
        
           
    def _create_plan_executor_graph(self):
        
        return MultiAgentPlannerExecuteGraph(
                 state_schema=PlanExecuteState,
                 model=self._llm,
                 output_schema=HistoricalResearchExecutionResult,
                 system_prompt=system_prompts["spec_multiagent_planner"].system_prompt,
                 executor=LLMExecutor(retry_agent=self._retry_policy, llm_timeout_seconds=self._llm_settings.llm_timeout_seconds),
                 stop_controller=StopController(),
                 checkpointer=self._checkpointer,
                 workers=self._workers,
                 plan_schema=HistoricalHypothesisEvaluationPlan,
                 tools=self._tools 
        ).build()
      
    
    def _create_agent_runner(self, compiled_graph) -> AgentGraphRunner:
        agent_settings = AgentRuntimeSettings(timeout_seconds=420)
        return AgentGraphRunner(
            graph=compiled_graph,
            settings = agent_settings,
            stop_controller=StopController(),
            trajectory_logger=TrajectoryLogger(agent_settings.trajectory_log_directory)
        )
    
    def _create_mas_initial_state(self, query: str):
            return {
                "query": query,
                "research_result": None,
                "critic_decision": None,
                "human_decision": None,
            }  
    def _get_initial_planer_state(self, query: str) ->PlanExecuteState:
        return {
                "messages": [
                    HumanMessage(
                        content=(
                            query
                        )
                    )
                ],
                "step_count": 0,
                "used_tokens": 0,
                "execution_status": PlanStepStatus.PENDING,
                "current_step_idx": 0,
                "current_step_result": None,
                "errors": [],
                "evaluated_current_step": None,
                "evaluated_steps":[],
                "executor_response": None,
                "len_steps": 0,
                "metadata": {},
                "plan": None,
                "plan_execution_evaluated": None,
                "results": [],
                "revised_plans":[],
                "structured_response": None,
                "user_task":query,
                "execution_id":str(uuid4()),
                "step_messages_start_idx": 0,
                "human_deсision": None,
                "interrupt_reason": None,
                "source_interrupt": SourceInterrupt.NO_SOURCE,
                
                
            }
       
    def _run_human_node(self, state: StateT) -> Command[Literal["superviser"]]:
        """Виконує HITL для демонстрації людині результату"""
        critic_decision = state["critic_decision"]

        human_response = interrupt(
        {
            "type": "critical_review",
            "reason": critic_decision.reason,
            "issues": critic_decision.issues,
            "recommendations": critic_decision.recommendations,
            "research_result": state["research_result"],
        }
    )

        human_decision = HumanReviewDecision.model_validate(
                                human_response
                             )

        return Command(
            update={
                "human_decision": human_decision,
            },
            goto="superviser",
        )
    
    async def run(self, thread_id: str, user_task: str):
        self._user_task = user_task
        return await self._runner.run(
            initial_state=self._create_mas_initial_state(self._user_task),
            thread_id=thread_id
        )
    
    async def resume(self, thread_id: str, decision: HumanReviewDecision):
        """Відновлює потік виконання після HITL"""
        return await self._runner.resume(
            thread_id=thread_id,
            decision=decision
        )
    
    def _build(self):
        
        graph = StateGraph(self._state_schema)
        
        graph.add_node(
            "plan_executor",
            self._run_plan_executor
        )
        graph.add_node(
            "critical_agent",
            self._critical_agent.execute
        )
        graph.add_node(
            "superviser",
            self._superviser.execute
        )
        graph.add_node(
            "human_review",
            self._run_human_node
        )
        graph.add_edge(
            START,
            "superviser"
        )
        
        return graph.compile(checkpointer=self._checkpointer)