from typing import Literal
from langgraph.types import Command
from langgraph.constants import END

from src.woolf_agents.domains.artifacts.schemas.contracts import CriticDecision, HistoricalResearchExecutionResult, SourceVerificationResult
from src.woolf_agents.workflows.state import MASAgentState, MASAgentStatus



class HistoricalSuperviser:
    
    def __init__(self):
        pass 
    
    async def execute(self, state: MASAgentState) ->Command[
                                                    Literal
                                                    [
                                                        "plan_executor",
                                                        "verification_agent",
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
        verification_sources: SourceVerificationResult = MASAgentState(state).get("verification_sources")
        if verification_sources is None:
            return Command(
                goto="verification_agent"
            )
        
        decision: CriticDecision = MASAgentState(state).get("critic_decision")
        if decision is None:
            return Command(
                goto="critical_agent"
            )
        
        if decision.decision == "approve":
            return Command(
                update ={
                  "status": MASAgentStatus.COMPLETED  
                },
                goto="__end__"
            )
        
        if decision.decision == "human_decision":
            return Command(
                update={
                    "status": MASAgentStatus.INTERRUPT
                },
                goto="human_review"
            )