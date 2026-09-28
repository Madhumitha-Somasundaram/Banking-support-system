import json

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from app.agents.main.state import AgentState
from app.agents.main.worker_tools import create_worker_tools

from shared.context import SecurityContext
from app.llm.client import llm


def build_graph(
    context: SecurityContext,
    conversation_id: int,
):

    tools = create_worker_tools(
        context=context,
        conversation_id=conversation_id,
    )

    llm_with_tools = llm.bind_tools(tools)

    async def call_main_agent(
        state: AgentState,
    ):

        response = await llm_with_tools.ainvoke(
            [
                {
                    "role": "system",
                    "content": """
You are the Main Banking Support Agent.

Your job is to understand the user's request and delegate
the request to the correct specialist agent.

Available specialists:

1. Account Support
- account balance
- account details
- account status
- account limits
- listing accounts

2. Transaction Support
- transaction history
- transaction details
- transaction status
- transaction-related questions

3. Card Support
- list cards
- card details
- card status
- card limits
- freeze card
- unfreeze card

4. RAG Support
- banking policies
- FAQs
- documentation
- general banking knowledge
- questions requiring knowledge-base retrieval

Rules:

- Never invent banking information.
- Always delegate banking-specific requests to the appropriate specialist.
- Do not expose internal service architecture.
- Do not expose internal MCP details.
- Respect the user's authorization and ownership.
""",
                },
                *state["messages"],
            ]
        )

        return {
            "messages": [response],
        }

    def route_after_tools(state: AgentState):

        last_message = state["messages"][-1]

        content = getattr(
            last_message,
            "content",
            "",
        )

        if not isinstance(content, str):
            return "main_agent"

        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return "main_agent"

        if data.get("status") == "APPROVAL_REQUIRED":
            return END

        return "main_agent"

    graph = StateGraph(AgentState)

    graph.add_node(
        "main_agent",
        call_main_agent,
    )

    graph.add_node(
        "tools",
        ToolNode(tools),
    )

    graph.add_edge(
        START,
        "main_agent",
    )

    graph.add_conditional_edges(
        "main_agent",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "main_agent": "main_agent",
            END: END,
        },
    )

    return graph.compile()