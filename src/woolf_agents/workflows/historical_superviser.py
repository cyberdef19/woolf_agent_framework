from typing import Literal
from langgraph.types import Command
from langgraph.constants import END

from src.woolf_agents.domains.artifacts.schemas.contracts import CriticDecision, HistoricalResearchExecutionResult
from src.woolf_agents.workflows.state import MASAgentState



class HistoricalSuperviser:
    
    def __init__(self):
        pass 
    
    async def execute(self, state: MASAgentState) ->Command[
                                                    Literal
                                                    [
                                                        "plan_executor",
                                                        "critical_agent",
                                                        "human_review",
                                                        "__end__"
                                                    ]
                                                    ]:
        research_result: HistoricalResearchExecutionResult = MASAgentState(state).get("research_result")
        if research_result is None:
            return Command(
                goto="plan_executor"
            )
        
        decision: CriticDecision = MASAgentState(state).get("critic_decision")
        if decision is None:
            return Command(
                goto="critical_agent"
            )
        
        if decision.decision == "approve":
            return Command(
                goto="__end__"
            )
        
        if decision.decision == "human_decision":
            return Command(
                goto="human_review"
            )