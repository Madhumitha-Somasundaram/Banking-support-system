
from shared.context import SecurityContext
from app.mcp.client import MCPClient


class RAGAgent:

    def __init__(
        self,
        context: SecurityContext,
    ):
        self.context = context

        self.mcp_client = MCPClient(
            context=context,
        )

    async def run(
        self,
        request: str,
    ) -> dict:

        tools = await self.mcp_client.get_tools(
            "rag"
        )

        answer_tool = next(
            tool
            for tool in tools
            if tool.name == "answer_question"
        )

        result = await answer_tool.ainvoke(
            {
                "question": request,
            }
        )

        return result

