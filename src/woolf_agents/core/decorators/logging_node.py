import logging
from time import perf_counter
from functools import wraps
from typing import TypeVar

StateT = TypeVar("StateT")
logger = logging.Logger(__name__)

def require_state(*required_fields: str):
    def decorator(func):

        @wraps(func)
        async def wrapper(self, state:StateT, *args, **kwargs):

            missing = [
                field
                for field in required_fields
                if field not in state
            ]

            if missing:
                raise ValueError(
                    f"Відсутні обов'язкові поля state: {missing}"
                )

            return await func(
                self,
                state,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator

def logging_node(name:str):
    def decorator(func):
        @wraps(func)
        async def wrapper(self, state: StateT, *args, **kwargs):
            started = perf_counter()
            print("ENTER NODE:", name)
            logger.info(
                "Node '%s' started. execution_id=%s",
                name,
                state.get("execution_id"),
            )

            try:
                result = await func(
                    self,
                    state,
                    *args,
                    **kwargs,
                )

                logger.info(
                    "Node '%s' completed in %.3f s",
                    name,
                    perf_counter() - started,
                )
                
                print(
                    "EXIT NODE:",
                    name,
                    "RESULT:",
                    result,
                    "TYPE:",
                    type(result),
                )

                return result

            except Exception:
                logger.exception(
                    "Node '%s' failed",
                    name,
                )
                raise

        return wrapper

    return decorator

