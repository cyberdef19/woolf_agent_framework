import re


class OutputGuard:


    _EMAIL = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    )

    _PHONE = re.compile(
        r"(?<!\w)"
        r"(?:\+?380|0)"
        r"[\s\-()]?"
        r"\d{2}"
        r"[\s\-()]?"
        r"\d{3}"
        r"[\s\-()]?"
        r"\d{2}"
        r"[\s\-()]?"
        r"\d{2}"
        r"(?!\w)"
    )

    _IPV4 = re.compile(
        r"\b"
        r"(?:"
        r"(?:25[0-5]|2[0-4]\d|1?\d?\d)\."
        r"){3}"
        r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"
        r"\b"
    )

    _CARD = re.compile(
        r"(?<!\d)"
        r"(?:\d[ -]*?){13,19}"
        r"(?!\d)"
    )

    def redact(self, text: str) -> str:
        if not isinstance(text, str):
            raise TypeError("Output must be a string.")

        text = self._EMAIL.sub(
            "[REDACTED_EMAIL]",
            text,
        )

        text = self._PHONE.sub(
            "[REDACTED_PHONE]",
            text,
        )

        text = self._IPV4.sub(
            "[REDACTED_IP]",
            text,
        )

        text = self._CARD.sub(
            "[REDACTED_CARD]",
            text,
        )

        return text