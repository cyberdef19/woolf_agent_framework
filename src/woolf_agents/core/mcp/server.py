from abc import ABC, abstractmethod
from fastmcp import FastMCP
from fastmcp.server.middleware.logging import StructuredLoggingMiddleware
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
from fastmcp.server.middleware.rate_limiting import RateLimitingMiddleware
from src.woolf_agents.core.mcp.middlewares.audit_middleware import AuditMiddleware
from src.woolf_agents.core.mcp.schemas.middleware_schemas import RateLimittingArgs


class BaseFastMCP(ABC):
    
    def __init__(self, name: str, instructions: str):
        
        self._mcp = FastMCP(
            name=name,
            instructions=instructions
        )
        
        self._register_core_middlewares()
        self._register_providers()
        
        
    
    def _register_core_middlewares(self)->None:
        """Реєструє middlware рівні"""
        #перехоплює виключення будь-якого внутрішнього шару
        self._mcp.add_middleware(
            ErrorHandlingMiddleware()
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
        
    
