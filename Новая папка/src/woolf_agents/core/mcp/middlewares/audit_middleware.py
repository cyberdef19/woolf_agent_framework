from fastmcp.server.middleware import Middleware, MiddlewareContext
from src.woolf_agents.core.mcp.decorators.audit_tool_calls import audit_tool_call

class AuditMiddleware(Middleware):
    
    @audit_tool_call
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        return await call_next(context)
        