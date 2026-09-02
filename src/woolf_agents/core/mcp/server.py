from abc import ABC, abstractmethod
from fastmcp import FastMCP
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from src.woolf_agents.core.mcp.middlewares.audit_middleware import AuditMiddleware
from src.woolf_agents.core.mcp.schemas.middleware_schemas import RateLimittingArgs, ErrorHandlingArgs
from src.woolf_agents.core.mcp.providers.langchain_tool_provider import LangchainToolProvider
from src.woolf_agents.tools.retriever_tools import retrieve_historical_sources, get_adjacent_chunks, search_related_sources
from src.woolf_agents.tools.web_retriever_tools import search_web_historical_sources



class BaseFastMCP(ABC):
    
    def __init__(self, name: str, instructions: str):
        
        self._mcp = FastMCP(
            name=name,
            instructions=instructions
        )
        
        self._register_core_middlewares()
        self._register_providers()
    
    @property
    def mcp(self)->FastMCP:
        return self._mcp
           
        
    
    def _register_core_middlewares(self)->None:
        """Реєструє middlware рівні"""
        #перехоплює виключення будь-якого внутрішнього шару
        eha = ErrorHandlingArgs()
        self._mcp.add_middleware(
            ErrorHandlingMiddleware(
                include_traceback=eha.include_traceback,
                transform_errors=eha.transform_errors
            )
        )
        #формує структуровані json логи
        self._mcp.add_middleware(
            StructuredLoggingMiddleware()
        )
        #реєструє помилки
        self._mcp.add_middleware(
            AuditMiddleware()
        )
        rla = RateLimittingArgs()
        #контролює частоту запитів
        self._mcp.add_middleware(
            RateLimitingMiddleware(
                max_requests_per_second=rla.max_requests_per_sec,
                burst_capacity=rla.burst_capacity
            )
        )
    
    
    @abstractmethod
    def _register_providers(self) -> None:
        ...
        
    
class HistoricalMCPServer(BaseFastMCP):
    
    def __init__(self, 
                 name, 
                 instructions
                 ):
        super().__init__(
            name, 
            instructions
            )
    
    def _register_providers(self):
        """Реєструє поровайдерів"""
        retriver_provider = LangchainToolProvider(
                        [
                            retrieve_historical_sources,
                            get_adjacent_chunks,
                            search_related_sources
                        ]
                    )
       
        web_retriever_provider = LangchainToolProvider(
                      [
                          search_web_historical_sources
                      ] 
        )
        self._mcp.add_provider(
            retriver_provider
        )
        
        self._mcp.add_provider(
            web_retriever_provider
        )

