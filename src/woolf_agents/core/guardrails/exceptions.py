class GuardrailError(Exception):
    """Базовий клас для guardrails"""


class InputGuardViolation(GuardrailError):
    """Raise коли детектиться небезпечний ввід"""


class ToolGuardViolation(GuardrailError):
    """Raise коли виклик інструмента не співпадає з політикою виклику інструментів."""