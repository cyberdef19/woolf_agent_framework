# evaluation/test_runner.py

from __future__ import annotations

import time
import asyncio
import json

from typing import Any

from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field

from src.woolf_agents.runtime.runner import AgentGraphRunner
from .test_case import AgentTestCase
from .test_result import AgentTestResult
from .evalution import evaluate_test_result, extract_tool_calls
    
from datetime import datetime, timezone
from pathlib import Path



class AgentTestRunner:
    """Execute agent test cases and collect comparable metrics."""

    def __init__(
        self,
        runner: AgentGraphRunner,
    ) -> None:
        self._runner = runner

    async def run_case(
        self,
        test_case: AgentTestCase,
    ) -> AgentTestResult:
        """Execute one test case."""

        initial_state = {
            "messages": [
                HumanMessage(
                    content=test_case.input_query,
                )
            ],
            "step_count": 0,
            "used_tokens": 0,
            "execution_status": "running",
        }

        started_at = time.perf_counter()

        try:
            final_state = await self._runner.run(
                initial_state
            )

            elapsed = (
                time.perf_counter() - started_at
            )

            messages = final_state.get(
                "messages",
                [],
            )

            tool_calls = extract_tool_calls(
                messages
            )

            actual_result = final_state.get(
                "structured_response"
            )

            passed = evaluate_test_result(
                test_case=test_case,
                final_state=final_state,
                tool_calls=tool_calls,
            )

            return AgentTestResult(
                case_id=test_case.case_id,
                input_query=test_case.input_query,
                expected_result=(
                    test_case.expected_result
                ),
                actual_result=self._serialize_result(
                    actual_result
                ),
                passed=passed,
                execution_status=final_state.get(
                    "execution_status",
                    "unknown",
                ),
                step_count=final_state.get(
                    "step_count",
                    0,
                ),
                tool_calls=tool_calls,
                execution_time_seconds=round(
                    elapsed,
                    4,
                ),
                used_tokens=final_state.get(
                    "used_tokens",
                    0,
                ),
            )

        except Exception as exc:
            elapsed = (
                time.perf_counter() - started_at
            )

            return AgentTestResult(
                case_id=test_case.case_id,
                input_query=test_case.input_query,
                expected_result=(
                    test_case.expected_result
                ),
                passed=False,
                execution_status="failed",
                execution_time_seconds=round(
                    elapsed,
                    4,
                ),
                error=f"{type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _serialize_result(
        result: Any,
    ) -> Any:
        if isinstance(result, BaseModel):
            return result.model_dump(
                mode="json"
            )

        return result



class AgentTestSuiteResult(BaseModel):
    """Aggregated evaluation report."""

    started_at: str
    finished_at: str

    total_cases: int
    passed_cases: int
    failed_cases: int

    results: list[AgentTestResult] = Field(
        default_factory=list,
    )


class AgentTestSuiteRunner:
    """Run test cases sequentially and persist one JSON report."""

    def __init__(
        self,
        *,
        test_runner: AgentTestRunner,
        output_path: Path,
    ) -> None:
        self._test_runner = test_runner
        self._output_path = output_path

    async def run(
        self,
        test_cases: list[AgentTestCase],
    ) -> AgentTestSuiteResult:
        started_at = self._now()

        results: list[AgentTestResult] = []

        for test_case in test_cases:
            result = await self._test_runner.run_case(
                test_case
            )
            results.append(result)

        suite_result = AgentTestSuiteResult(
            started_at=started_at,
            finished_at=self._now(),
            total_cases=len(results),
            passed_cases=sum(
                result.passed
                for result in results
            ),
            failed_cases=sum(
                not result.passed
                for result in results
            ),
            results=results,
        )

        await asyncio.to_thread(
            self._write_report,
            suite_result,
        )

        return suite_result

    def _write_report(
        self,
        report: AgentTestSuiteResult,
    ) -> None:
        self._output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._output_path.write_text(
            json.dumps(
                report.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()