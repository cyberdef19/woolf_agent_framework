from __future__ import annotations

import hashlib
import json
import time
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StopReason(StrEnum):
    MAX_STEPS = "max_steps"
    MAX_TOKENS = "max_tokens"
    TIMEOUT = "timeout"
    REPEATED_TOOL_CALL = "repeated_tool_call"


class StopDecision(BaseModel):
    """Result of evaluating agent execution stop conditions."""

    model_config = ConfigDict(frozen=True)

    should_stop: bool = Field(
        description="Whether the current agent execution must stop.",
    )

    reason: StopReason | None = Field(
        default=None,
        description="Machine-readable reason for stopping the execution.",
    )

    message: str | None = Field(
        default=None,
        description="Human-readable explanation of the stop decision.",
    )


class StopController:
    """Track one agent run and enforce configured execution limits."""

    def __init__(
        self,
        *,
        max_steps: int = 10,
        max_tokens: int = 50_000,
        timeout_seconds: float = 2400.0,
        max_consecutive_repeats: int = 6,
    ) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1.")

        if max_tokens < 1:
            raise ValueError("max_tokens must be at least 1.")

        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive.")

        if max_consecutive_repeats < 2:
            raise ValueError(
                "max_consecutive_repeats must be at least 2."
            )

        self.max_steps = max_steps
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds
        self.max_consecutive_repeats = max_consecutive_repeats

        self.reset()

    def reset(self) -> None:
        """Reset mutable state before starting a new agent run."""

        self._started_at = time.monotonic()
        self._tool_call_history: list[str] = []

    def evaluate(
        self,
        *,
        completed_steps: int,
        used_tokens: int,
        tool_calls: list[dict[str, Any]],
    ) -> StopDecision:
        """Evaluate all configured stop conditions."""

        if completed_steps >= self.max_steps:
            return StopDecision(
                should_stop=True,
                reason=StopReason.MAX_STEPS,
                message=(
                    "Виконання зупинено: досягнуто максимальну "
                    f"кількість кроків ({self.max_steps})."
                ),
            )

        if used_tokens >= self.max_tokens:
            return StopDecision(
                should_stop=True,
                reason=StopReason.MAX_TOKENS,
                message=(
                    "Виконання зупинено: вичерпано бюджет токенів "
                    f"({used_tokens} із {self.max_tokens})."
                ),
            )

        elapsed = time.monotonic() - self._started_at

        if elapsed >= self.timeout_seconds:
            return StopDecision(
                should_stop=True,
                reason=StopReason.TIMEOUT,
                message=(
                    "Виконання зупинено через перевищення загального "
                    f"тайм-ауту ({self.timeout_seconds:.1f} с)."
                ),
            )

        fingerprints = [
            self._fingerprint_tool_call(tool_call)
            for tool_call in tool_calls
        ]

        self._tool_call_history.extend(fingerprints)

        if self._has_consecutive_repetition():
            return StopDecision(
                should_stop=True,
                reason=StopReason.REPEATED_TOOL_CALL,
                message=(
                    "Виконання зупинено: агент повторює той самий "
                    "виклик інструмента."
                ),
            )

        return StopDecision(
            should_stop=False,
        )

    def _has_consecutive_repetition(self) -> bool:
        recent = self._tool_call_history[
            -self.max_consecutive_repeats:
        ]

        return (
            len(recent) == self.max_consecutive_repeats
            and len(set(recent)) == 1
        )

    @staticmethod
    def _fingerprint_tool_call(
        tool_call: dict[str, Any],
    ) -> str:
        payload = json.dumps(
            {
                "name": tool_call["name"],
                "args": tool_call.get("args", {}),
            },
            sort_keys=True,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()