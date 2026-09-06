from typing import Literal, Annotated
from typing_extensions import NotRequired
from src.woolf_agents.workflows.state import MessageAgentState
from src.woolf_agents.core.result import BaseExecutionResult
from src.woolf_agents.domains.artifacts.schemas.contracts import MetadataFileResult, FileHashResult, ExtractedStringsResult
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
    structured_response: NotRequired[BaseExecutionResult]
    metadata_result: NotRequired[MetadataFileResult]
    hashing_result: NotRequired[FileHashResult]
    extracted_result: NotRequired[ExtractedStringsResult]
    summary: NotRequired[str]
    