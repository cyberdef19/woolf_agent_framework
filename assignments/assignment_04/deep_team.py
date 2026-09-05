from uuid import uuid4

from deepteam import red_team
from deepteam.vulnerabilities import (
    PromptLeakage,
    Robustness,
    ToolOrchestrationAbuse,
)
from deepteam.attacks.single_turn import PromptInjection
from deepteam.red_teamer.red_teamer import RedTeamer

from src.woolf_agents.core.guardrails.exceptions import InputGuardViolation
from .langchain_deep_eval_llm import LangChainDeepEvalLLM


async def create_model_callback(mas):

    async def model_callback(input: str) -> str:
        try:
            result = await mas.run(
                thread_id=str(uuid4()),
                user_task=input,
            )
            return result.answer or str(result)

        except InputGuardViolation:
            return "Request blocked by security policy."

        except Exception as exc:
            return f"Request failed safely: {type(exc).__name__}"

    return model_callback


async def run_red_team(mas, llm):
    
    deepteam_llm = LangChainDeepEvalLLM(llm)
    
    redteamer = RedTeamer(
        target_purpose=""" "Мультиагентна система історичних досліджень 
                    Система отримує історичні джерела через MCP інструменти, 
                    аналізує історичні гіпотези, оцінює докази, 
                    і надає висновок на основі наявних історичних доказів.""",
        simulator_model=deepteam_llm,
        evaluation_model=deepteam_llm
    )
    

    model_callback = await create_model_callback(mas)
    vulners = [
            PromptLeakage(
                types=[
                    "instructions",
                    "guard_exposure",
                ],
                simulator_model=deepteam_llm,
                evaluation_model=deepteam_llm
            ),

            Robustness(
                types=[
                    "hijacking",
                ],
                simulator_model=deepteam_llm,
                evaluation_model=deepteam_llm
            ),

            ToolOrchestrationAbuse(
                types=[
                    "recursive_tool_calls",
                    "tool_budget_exhaustion",
                ],
                simulator_model=deepteam_llm,
                evaluation_model=deepteam_llm
            ),
        ]
    
    print("\n=== DEEPTEAM DIAGNOSTICS ===")
    print("DeepTeam wrapper:", type(deepteam_llm))
    print("Wrapped LLM:", type(deepteam_llm.load_model()))

    for vulner in vulners:
        print(f"\nVulnerability: {type(vulner).__name__}")

        print(
            "  simulator_model:",
            type(vulner.simulator_model),
        )

        print(
            "  evaluation_model:",
            type(vulner.evaluation_model),
        )

    print("============================\n")

    # ===== RED TEAM =====

    risk_assessment = redteamer.red_team(
        model_callback=model_callback,
        vulnerabilities=vulners,
        attacks=[
            PromptInjection(),
        ],
        attacks_per_vulnerability_type=1,
        
    )

    return risk_assessment