from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from shared.context import SecurityContext
from shared.internal_token import create_internal_token
from shared.config import settings


class MCPClient:
    """
    Reusable MCP client for connecting agents to MCP servers.
    """

    def __init__(
        self,
        context: SecurityContext,
    ):
        self.context = context

        internal_token = create_internal_token(
    user_id=context.user_id,
    role=context.role,
    conversation_id=context.conversation_id,
)

        print(
            f"[MCP CLIENT DEBUG] "
            f"user_id={context.user_id}, role={context.role}"
        )

        self.internal_headers = {
            "Authorization": f"Bearer {internal_token}",
        }

    async def get_tools(
        self,
        server_name: str,
    ) -> list[BaseTool]:
        """
        Get tools from the requested MCP server.
        """

        servers = {
            "account": {
                "url": settings.ACCOUNT_MCP_URL,
                "transport": "streamable_http",
                "headers": self.internal_headers,
            },
            "transaction": {
                "url": settings.TRANSACTION_MCP_URL,
                "transport": "streamable_http",
                "headers": self.internal_headers,
            },
            "card": {
                "url": settings.CARD_MCP_URL,
                "transport": "streamable_http",
                "headers": self.internal_headers,
            },
            "rag":{
                "url": settings.RAG_MCP_URL,
                "transport": "streamable_http",
                "headers": self.internal_headers,
            }
        }

        if server_name not in servers:
            raise ValueError(
                f"Unknown MCP server: {server_name}"
            )

        client = MultiServerMCPClient(
            {
                server_name: servers[server_name],
            }
        )

        return await client.get_tools()