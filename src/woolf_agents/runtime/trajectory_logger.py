from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel


class TrajectoryLogger:
    """Persist LangGraph node updates as a JSON trajectory."""

    def __init__(self, log_directory: Path) -> None:
        self._log_directory = log_directory

    async def run_and_log(
        self,
        *,
        graph: CompiledStateGraph,
        initial_state: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        run_id = str(uuid4())
        started_at = self._now()
        trajectory: list[dict[str, Any]] = []

        final_state: dict[str, Any] = {}
        
        path = self._log_directory / f"{run_id}.json"
        error: str|None = None
        try:

            async for event in graph.astream(
                initial_state,
                config=config,
                stream_mode="updates",
            ):
                serialized_event = self._serialize(event)

                trajectory.append(
                    {
                        "timestamp": self._now(),
                        "update": serialized_event,
                    }
                )

                # stream_mode="updates" повертає оновлення за іменами вузлів.
                if isinstance(serialized_event, dict):
                    for node_update in serialized_event.values():
                        if isinstance(node_update, dict):
                            final_state.update(node_update)
            return final_state
        except BaseException as ex:
            error = f"{type(ex).__name__}: {ex}"
            raise
        finally:
            document = {
                "run_id": run_id,
                "started_at": started_at,
                "finished_at": self._now(),
                "initial_state": self._serialize(initial_state),
                "trajectory": trajectory,
                "final_state": self._serialize(final_state),
                "error": error
            }

       

            await asyncio.to_thread(
                self._write_json,
                path,
                document,
            )

       

    @staticmethod
    def _write_json(
        path: Path,
        document: dict[str, Any],
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            json.dumps(
                document,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def _serialize(cls, value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")

        if isinstance(value, dict):
            return {
                str(key): cls._serialize(item)
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                cls._serialize(item)
                for item in value
            ]

        if isinstance(
            value,
            (str, int, float, bool, type(None)),
        ):
            return value

        if hasattr(value, "model_dump"):
            return value.model_dump(mode="json")

        return str(value)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()