
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.main.state import AgentState
from app.llm.client import llm
from shared.context import SecurityContext
from app.mcp.client import MCPClient


async def build_transaction_graph(
    context: SecurityContext,
):
    """
    Build the Transaction Support Agent.

    The agent uses tools exposed by the
    Transaction MCP server.
    """

    # Create MCP client with the current security context.
    mcp_client = MCPClient(
        context=context,
    )

    # Get Transaction MCP tools.
    tools = await mcp_client.get_tools(
        "transaction"
    )

    # Give Transaction tools to the LLM.
    llm_with_tools = llm.bind_tools(tools)

    async def call_transaction_agent(
        state: AgentState,
    ):
        response = await llm_with_tools.ainvoke(
            [
                SystemMessage(
                    content="""
You are the Transaction Support Agent.

You handle:
- transaction history
- transaction details
- transaction search
- pending transactions
- transaction summaries
- transaction disputes

TRANSACTION SELECTION RULES:

1. If the user asks for ALL transactions:
   Use the appropriate transaction history/search MCP tool.

2. If the user provides a transaction identifier:
   Use the appropriate transaction MCP tool.

3. If the user asks about transactions for a specific
   account, use the account identifier when available.

4. If the user asks about a transaction without enough
   information to identify it:
   - If exactly one transaction matches, return its information.
   - If multiple transactions match, ask the user for clarification.

5. Use MCP tools whenever actual banking information
   is required.

6. Never invent transaction information.

7. Only access transaction information belonging to
   the authenticated user.

8. Do not expose:
   - internal system details
   - security context
   - database details
   - authentication tokens
   - internal tool errors

9. If an MCP tool returns an error or no matching
   transaction exists, explain the result to the user
   without exposing internal implementation details.

10. For transaction disputes, provide the actual transaction
    information returned by the MCP tool. Do not claim that
    a dispute was created or resolved unless the MCP tool
    confirms the action.
"""
                ),
                *state["messages"],
            ]
        )

        return {
            "messages": [response]
        }

    graph = StateGraph(AgentState)

    graph.add_node(
        "transaction_agent",
        call_transaction_agent,
    )

    graph.add_node(
        "tools",
        ToolNode(tools),
    )

    graph.add_edge(
        START,
        "transaction_agent",
    )

    graph.add_conditional_edges(
        "transaction_agent",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )

    graph.add_edge(
        "tools",
        "transaction_agent",
    )

    return graph.compile()

