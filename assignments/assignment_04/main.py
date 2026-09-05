
import asyncio
import os

import aiosqlite
from uuid import uuid4
from assignments.assignment_04.deep_team import run_red_team
from src.woolf_agents.core.result import ExecutionStatus
from src.woolf_agents.core.retry import RetryPolicyAgent, RetrySettings
from src.woolf_agents.domains.artifacts.schemas.contracts import HumanReviewDecision
from src.woolf_agents.llm.config import ConfigLangsmithAPI, ConfigModelAPI, LLMModel, LLMProvider, LLMSettings, LangSmithSettings
from src.woolf_agents.llm.executor import LLMExecutor
from src.woolf_agents.llm.factory import LLMFactory
from src.woolf_agents.workflows.mas_research_graph import MASResearchGraph
from src.woolf_agents.workflows.state import MASAgentState
from src.woolf_agents.llm.settings import url_modelrouter
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_mcp_adapters.client import MultiServerMCPClient

settings = LLMSettings(
    provider=LLMProvider.OPENROUTER,
    model = LLMModel.GPTOMINI4O,
    base_url=url_modelrouter["openrouter_url"],
    api_key = ConfigModelAPI.OPENROUTERKEY
)
llm = LLMFactory.create(settings=settings)

retry_policy = RetryPolicyAgent(
    settings=RetrySettings()
)

def configure_langsmith(
    settings: LangSmithSettings,
) -> None:
    if not settings.enabled:
        os.environ["LANGSMITH_TRACING"] = "false"
        return
    
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.api_key
    os.environ["LANGSMITH_PROJECT"] = settings.project
    os.environ["LANGSMITH_ENDPOINT"] = settings.endpoint

async def main():
    
    configure_langsmith(
            settings=LangSmithSettings(
                enabled=True,
                api_key=ConfigLangsmithAPI.LANGSMITHKEY,
                project="HistoricalHypothesisAgent"
            )
    )
    connection = await aiosqlite.connect(
        "src\\woolf_agents\\data\checkpoints\\checkpoints.sqlite"
    )
    checkpointer = AsyncSqliteSaver(
        connection
    )

    mcp_client = MultiServerMCPClient({
    "historical": {
        "transport": "stdio",
        "command": "python",
        "args": [
            "-m",
            "src.woolf_agents.core.mcp.server"
        ]
        }
        }
    )
    
    mas: MASResearchGraph = MASResearchGraph(
        state_schema=MASAgentState,
        llm=llm,
        checkpointer=checkpointer,
        executor=LLMExecutor(retry_agent=retry_policy, llm_timeout_seconds=settings.llm_timeout_seconds),
        mcp_client=mcp_client,
        retry_policy=retry_policy
    )
    
    user_task="Яке походження назви Хаджибей? Визнач представлені в доступних джерелах гіпотези та оціни, яка з них має найкращу доказову підтримку."
    thread_id = str(uuid4())
    result = await mas.run(
        thread_id=thread_id,
        user_task=user_task
    )

    
    if result.status == ExecutionStatus.INTERRUPT:
        print("\nCritical Agent requests human review.")

        if result.critic_decision:
            print("\nReason:")
            print(result.critic_decision.reason)

            print("\nIssues:")
            for issue in result.critic_decision.issues:
                print(f"- {issue}")

            print("\nRecommendations:")
            for recommendation in result.critic_decision.recommendations:
                print(f"- {recommendation}")

        answer = input(
            "\nApprove research result? [y/n]: "
        ).strip().lower()

        decision = HumanReviewDecision(
            decision="approve" if answer == "y" else "reject"
        )
        result = await mas.resume(
            thread_id=thread_id,
            decision=decision,
        )
    print("\nFINAL RESULT:")
    print(result)
    
    #risk_assessment = await run_red_team(mas, llm)

    #print(risk_assessment)


if __name__=="__main__":
    asyncio.run(main())