from langchain_core.tools import StructuredTool, Tool
from collections.abc import Sequence

class LangchainToMCPTool:
    
    @staticmethod
    def langchain_to_mcp_tool_adapter(tool: StructuredTool) -> Tool:
        """Адаптує langchain інструмент в mcp інструмент"""
        
        callable_fn = tool.coroutine or tool.func
        
        if callable_fn is None:
            raise ValueError(
                f"Tool '{tool.name}' has no callable function."
            )
        
        return Tool.from_function(
            func=callable_fn,
            name=tool.name,
            description=tool.description
        )
    
    @classmethod
    def batch_langchain_to_mcp_tool_adapter(cls, tools: Sequence[StructuredTool]) -> Tool:
        """Масове перетворення інструментів"""
        return [cls.langchain_to_mcp_tool_adapter(tool) for tool in tools]
        
        