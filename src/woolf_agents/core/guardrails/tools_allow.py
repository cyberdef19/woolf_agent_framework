from collections.abc import Iterable, Mapping
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import ValidationError

from .exceptions import ToolGuardViolation


class ToolGuard:


    def __init__(
        self,
        tools: Iterable[BaseTool],
        allowed_tools: Iterable[str],
    ) -> None:
        self._tools = {
            tool.name: tool
            for tool in tools
        }

        self._allowed_tools = frozenset(allowed_tools)

    def validate(
        self,
        tool_name: str,
        arguments: Mapping[str, Any],
    ) -> dict[str, Any]:

        if tool_name not in self._allowed_tools:
            raise ToolGuardViolation(
                f"Tool '{tool_name}' is not allowed."
            )

        tool = self._tools.get(tool_name)

        if tool is None:
            raise ToolGuardViolation(
                f"Tool '{tool_name}' is not available."
            )

        args = dict(arguments)

        schema = tool.args_schema

        if schema is None:
            return args

        try:
            validated = schema.model_validate(args)

        except ValidationError as exc:
            raise ToolGuardViolation(
                f"Invalid arguments for tool '{tool_name}'."
            ) from exc

        return validated.model_dump()