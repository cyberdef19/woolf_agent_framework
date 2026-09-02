import re
from collections.abc import Sequence

from .models import GuardResult


DEFAULT_INJECTION_PATTERNS: tuple[str, ...] = (
    r"\bignore\s+(all\s+)?previous\s+instructions?\b",
    r"\bignore\s+(all\s+)?prior\s+instructions?\b",
    r"\bforget\s+(all\s+)?previous\s+instructions?\b",
    r"\bdisregard\s+(all\s+)?previous\s+instructions?\b",

    r"\breveal\s+(the\s+)?system\s+prompt\b",
    r"\bshow\s+(me\s+)?(the\s+)?system\s+prompt\b",
    r"\bprint\s+(the\s+)?system\s+prompt\b",

    r"\bbypass\s+(the\s+)?(rules|restrictions|guardrails|security)\b",
    r"\bdisable\s+(the\s+)?(guardrails|security|restrictions)\b",

    r"\byou\s+are\s+now\s+(an?\s+)?unrestricted\b",
    r"\bact\s+as\s+(an?\s+)?unrestricted\b",
)


class InputGuard:
    """Детектимо спроби промпт ін'єкцій"""

    def __init__(
        self,
        patterns: Sequence[str] | None = None,
    ) -> None:
        source_patterns = patterns or DEFAULT_INJECTION_PATTERNS

        self._patterns = tuple(
            re.compile(pattern, flags=re.IGNORECASE)
            for pattern in source_patterns
        )

    def validate(self, text: str) -> GuardResult:
        if not isinstance(text, str):
            return GuardResult(
                allowed=False,
                reason="Input must be a string.",
            )

        normalized = " ".join(text.split())

        if not normalized:
            return GuardResult(
                allowed=False,
                reason="Input must not be empty.",
            )

        for pattern in self._patterns:
            if pattern.search(normalized):
                return GuardResult(
                    allowed=False,
                    reason="Потенційна промпт ін'єкція.",
                )

        return GuardResult(allowed=True)