from collections.abc import Iterable, Mapping
from typing import Any
from jsonschema import  ValidationError as JsonSchemaValidationError
from jsonschema import validate as validate_json_schema

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ValidationError

from src.woolf_agents.core.guardrails.exceptions import ToolGuardViolation


class ToolGuard:

    def __init__(
        self,
        tools: Iterable[BaseTool],
        allowed_tools: Iterable[str],
    ):
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

        # 1. Allowlist
        if tool_name not in self._allowed_tools:
            raise ToolGuardViolation(
                f"Tool '{tool_name}' is not allowed."
            )

        # 2. Tool exists
        tool = self._tools.get(tool_name)

        if tool is None:
            raise ToolGuardViolation(
                f"Tool '{tool_name}' is not available."
            )

        args = dict(arguments)

        schema = tool.args_schema

        if schema is None:
            return args

        # 3. Pydantic schema
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            try:
                validated = schema.model_validate(args)
            except ValidationError as exc:
                raise ToolGuardViolation(
                    f"Invalid arguments for tool '{tool_name}'."
                ) from exc

            return validated.model_dump()

        # 4. MCP/LangChain JSON schema
        if isinstance(schema, dict):
            self._validate_json_schema(
                tool_name=tool_name,
                schema=schema,
                arguments=args,
            )

            return args

        raise ToolGuardViolation(
            f"Unsupported argument schema for tool '{tool_name}': "
            f"{type(schema).__name__}"
        )
    def _validate_json_schema(self, tool_name: str, schema: dict[str, Any],arguments: dict[str, Any]) -> None:

        try:
            validate_json_schema(
                instance=arguments,
                schema=schema,
            )

        except JsonSchemaValidationError as exc:
            raise ToolGuardViolation(
                f"Invalid arguments for tool '{tool_name}'."
            ) from exc