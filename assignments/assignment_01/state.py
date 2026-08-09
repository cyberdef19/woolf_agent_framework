from typing import Literal, Annotated
from typing_extensions import NotRequired
from src.woolf_agents.workflows.state import MessageAgentState
from .result import AssignmentResult01
from pathlib import Path


AnalysisStatus = Literal[
    "pending",
    "in_progress",
    "completed",
    "failed",
    "stopped"
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
    artifact_path: Path
    execution_status: NotRequired[AnalysisStatus]
    structured_response: NotRequired[AssignmentResult01]