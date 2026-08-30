from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any, Generic, TypeVar

from langgraph.errors import GraphRecursionError
from langgraph.graph.state import CompiledStateGraph

from .stop_controller import StopController
from .settings import AgentRuntimeSettings
from .trajectory_logger import TrajectoryLogger
from langgraph.types import Command

StateT = TypeVar("StateT", bound=Mapping[str, Any])


class AgentExecutionError(RuntimeError):
    """Base exception raised when a graph execution cannot complete."""


class AgentExecutionTimeoutError(AgentExecutionError):
    """Raised when the complete graph run exceeds its time limit."""


class AgentRecursionLimitError(AgentExecutionError):
    """Raised when LangGraph exceeds its recursion safety limit."""


class AgentGraphRunner(Generic[StateT]):
    """
    Execute a compiled LangGraph workflow with runtime safeguards.

    The runner does not define graph topology. It controls one graph run,
    applying an overall timeout, recursion protection and trajectory
    logging.
    """

    def __init__(
        self,
        *,
        graph: CompiledStateGraph,
        settings: AgentRuntimeSettings,
        stop_controller: StopController,
        trajectory_logger: TrajectoryLogger | None = None,
    ) -> None:
        self._graph = graph
        self._settings = settings
        self._stop_controller = stop_controller
        self._trajectory_logger = trajectory_logger

    async def run(
        self,
        initial_state: StateT,
        thread_id:str
    ) -> dict[str, Any]:
        """Run the graph asynchronously and return its final state."""

        self._stop_controller.reset()
        config=self._build_run_config(
                                thread_id=thread_id
                                )

        try:
            async with asyncio.timeout(
                self._settings.timeout_seconds
            ):
                if (
                    self._settings.trajectory_logging_enabled
                    and self._trajectory_logger is not None
                ):
                    return await self._run_with_trajectory(
                        initial_state,
                        config=config
                    )

                return await self._graph.ainvoke(
                    initial_state,
                    config=config
                )
               
                
        except TimeoutError as exc:
            raise AgentExecutionTimeoutError(
                "Виконання агента перевищило загальний тайм-аут "
                f"{self._settings.timeout_seconds} с."
            ) from exc

        except GraphRecursionError as exc:
            raise AgentRecursionLimitError(
                "LangGraph перевищив аварійний ліміт кроків "
                f"({self._settings.recursion_limit})."
            ) from exc
        

    async def _run_with_trajectory(
        self,
        initial_state: StateT,
        config:dict[str, Any]
    ) -> dict[str, Any]:
        """Run the graph while recording node updates."""

        assert self._trajectory_logger is not None

        return await self._trajectory_logger.run_and_log(
            graph=self._graph,
            initial_state=dict(initial_state),
            config=config,
        )

    def _build_run_config(self, thread_id: str) -> dict[str, Any]:
        """Build LangGraph runtime configuration."""

        return {
            "recursion_limit": self._settings.recursion_limit,
            "run_name": "HistoricalHypothesisAgent",
            "configurable":{
                "thread_id":thread_id
            }
        }
    async def resume(self, thread_id: str, decision: str) -> dict[str, Any]:

        config = self._build_run_config(
            thread_id=thread_id
        )

        return await self._graph.ainvoke(
            Command(
                resume=decision
            ),
            config=config,
        )