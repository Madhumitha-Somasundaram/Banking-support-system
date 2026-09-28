
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage

from app.agents.main.state import AgentState
from app.llm.client import llm
from shared.context import SecurityContext
from app.mcp.client import MCPClient


async def build_account_graph(
    context: SecurityContext,
):
    """
    Build the Account Support Agent.

    This agent is independently deployed and communicates
    with the Account MCP server through MCPClient.

    The agent does NOT access the account database directly.
    """

    # --------------------------------------------------
    # MCP CLIENT
    # --------------------------------------------------

    mcp_client = MCPClient(
        context=context,
    )

    # Get Account MCP tools.
    tools = await mcp_client.get_tools("account")

    # Bind MCP tools to the LLM.
    llm_with_tools = llm.bind_tools(tools)

    # --------------------------------------------------
    # ACCOUNT AGENT
    # --------------------------------------------------

    async def call_account_agent(state: AgentState):

        response = await llm_with_tools.ainvoke(
            [
                SystemMessage(
                    content="""
You are the Account Support Agent.

You handle:

- account balance
- account details
- account status
- account limits
- listing all accounts

ACCOUNT SELECTION RULES:

1. If the user asks about ALL accounts:

   Use the list_user_accounts MCP tool.

   Return information for every account owned by the
   authenticated user.

2. If the user identifies a specific account:

   Use the appropriate Account MCP tool with the
   account identifier provided by the user.

3. If the user asks an account-specific question without
   identifying an account:

   Use the appropriate MCP tool without an account
   identifier.

   - If exactly one account matches, return its information.
   - If multiple accounts match, ask the user which account
     they mean.

4. Never ask for an account number when the user explicitly
   asks about ALL accounts.

5. Never invent banking information.

6. Only access information belonging to the authenticated
   user.

7. Always use MCP tools for actual banking information.

8. Do not expose:

   - internal system details
   - security context
   - database details
   - authentication tokens
   - internal tool errors

9. If the MCP tool returns an error or no matching account,
   clearly explain the result without exposing internal
   implementation details.
"""
                ),
                *state["messages"],
            ]
        )

        return {
            "messages": [response],
        }

    # --------------------------------------------------
    # GRAPH
    # --------------------------------------------------

    graph = StateGraph(AgentState)

    graph.add_node(
        "account_agent",
        call_account_agent,
    )

    graph.add_node(
        "tools",
        ToolNode(tools),
    )

    # START
    graph.add_edge(
        START,
        "account_agent",
    )

    # Agent decides whether it needs an MCP tool.
    graph.add_conditional_edges(
        "account_agent",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )

    # MCP tool result goes back to Account Agent.
    graph.add_edge(
        "tools",
        "account_agent",
    )

    return graph.compile()

