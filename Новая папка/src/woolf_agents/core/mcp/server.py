    
from src.woolf_agents.core.mcp.servers.historical_mcp_server import HistoricalMCPServer

def main():
    historical_mcp =HistoricalMCPServer(
            name="historical_mcp_server",
            instructions="Надай інструменти для історичного дослідження"
        )
    historical_mcp.mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
    