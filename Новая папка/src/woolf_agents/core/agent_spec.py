from pydantic import BaseModel, ConfigDict, Field


class AgentSpec(BaseModel):
    """Декларативний опис для AI агента"""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )

    name: str = Field(
        min_length=1,
        description="Назва агента",
    )

    role: str = Field(
        min_length=1,
        description="Професійна роль, яку виконує агент",
    )

    goal: str = Field(
        min_length=1,
        description="Ціль, яку має досягнути агент",
    )

    instructions: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Оперативні інструкції для агента",
    )

    constraints: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Правила та обмеження, яких має притримуватися агент",
    )

    tool_names: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Назви інструментів для агента",
    )

    response_language: str = Field(
        default="ukrainian",
        description="Мова фінальної відповіді",
    )
    
    @property
    def system_prompt(self) -> str:
        """Створення системного промпта для агента"""

        sections = [
            f"Ти {self.name}.",
            self._build_section("Роль", (self.role,)),
            self._build_section("Мета", (self.goal,)),
            self._build_section(
                "Інструкціцї",
                self.instructions
                or ("Слідуй вимогам користувача точно (акуратно).",),
                use_bullets=True,
            ),
            self._build_section(
                "Правила",
                self.constraints
                or ("Не вигадуй інформацію.",),
                use_bullets=True,
            ),
            f"Respond in {self.response_language}.",
        ]

        return "\n\n".join(sections)

    @staticmethod
    def _build_section(
        title: str,
        values: tuple[str, ...],
        *,
        use_bullets: bool = False,
    ) -> str:
        

        normalized_values = tuple(
            value.strip()
            for value in values
            if value.strip()
        )

        if use_bullets:
            content = "\n".join(
                f"- {value}"
                for value in normalized_values
            )
        else:
            content = "\n".join(normalized_values)

        return f"{title}:\n{content}"
    
    