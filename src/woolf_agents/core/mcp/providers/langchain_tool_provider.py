from fastmcp.server.providers import Provider
from fastmcp.tools import Tool
from collections.abc import Sequence
from langchain_core.tools import StructuredTool
from src.woolf_agents.core.mcp.adapters.tools import LangchainToMCPTool


class LangchainToolProvider(Provider):
    
    def __init__(self,
                 tools: Sequence[StructuredTool]
                 ):
        super().__init__()
        
        self._tools = LangchainToMCPTool.batch_langchain_to_mcp_tool_adapter(tools=tools)
    
    @property
    async def tools(self)->Sequence[Tool]:
        return self._tools
        