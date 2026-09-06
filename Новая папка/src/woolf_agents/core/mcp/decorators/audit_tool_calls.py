import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)


def audit_tool_call(func):

    @wraps(func)
    async def wrapper(self, context, call_next):
        started_at = time.perf_counter()

        tool_name = context.message.name
        arguments = context.message.arguments or {}

        logger.info(
            "MCP tool call started: tool=%s args=%s",
            tool_name,
            list(arguments.keys()),
        )

        try:
            result = await func(
                self,
                context,
                call_next,
            )

            duration_ms = (
                time.perf_counter() - started_at
            ) * 1000

            logger.info(
                "MCP tool call completed: "
                "tool=%s duration_ms=%.2f",
                tool_name,
                duration_ms,
            )

            return result

        except Exception as exc:
            duration_ms = (
                time.perf_counter() - started_at
            ) * 1000

            logger.exception(
                "MCP tool call failed: "
                "tool=%s duration_ms=%.2f error=%s",
                tool_name,
                duration_ms,
                type(exc).__name__,
            )

            raise

    return wrapper