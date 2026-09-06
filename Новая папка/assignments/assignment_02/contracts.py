
from src.woolf_agents.domains.artifacts.schemas.contracts import HistoricalResearchStepPlan, HistoricalResearchPlan
from typing import Literal 
from pydantic import Field
"""class HypothesisEvaluationStep(HistoricalResearchStepPlan):
    Конкретний крок плану для оцінки гіпотези
    operation: Literal[
        "retrieve_sources",
        "extract_claims",
        "generate_hypotheses",
        "evaluate_hypotheses",
        "synthesize_conclusion"
        ] = Field(
            description=retrieve_sources-зосередься на пошуку релевантних історичних джерел.
                           якщо джерел у контексті немає, використовуй retrieval tools.
                           extract_claims-виділяй твердження, явно підтримані отриманими джерелами.
                           generate_hypotheses-сформуй альтернативні гіпотези на основі extracted claims.
                           evaluate_hypotheses-порівняй гіпотези з supporting та contradicting evidence.
                           synthesize_conclusion-сформуй висновок, не приховуючи невизначеність і альтернативні версії.
                    
            
        )

class HistoricalHypothesisEvaluationPlan(HistoricalResearchPlan):
    План для оцінки історичної гіпотези
    steps:list[HypothesisEvaluationStep]
"""