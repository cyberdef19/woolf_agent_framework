from typing import Literal, Annotated
from typing_extensions import NotRequired
from src.woolf_agents.workflows.state import MessageAgentState


AnalysisStatus = Literal[
    "pending",
    "in_progress",
    "completed",
    "failed",
]

class Assignment01AgentState(MessageAgentState, total=False):
    
    """State used by the digital artifact analysis workflow.

    Attributes:
        artifact_path:
            Path to the local file being analyzed.

        analysis_status:
            Current execution status of the workflow.

        final_report:
            Final human-readable artifact analysis report.
    """
    artifact_path: str
    analysis_status: NotRequired[AnalysisStatus]
    final_report: NotRequired[str]