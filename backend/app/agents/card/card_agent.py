
import json

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import interrupt

from langchain_core.messages import (
    SystemMessage,
    ToolMessage,
)

from app.agents.main.state import AgentState
from app.llm.client import llm
from shared.context import SecurityContext
from shared.authorization import get_authorization_service
from app.mcp.client import MCPClient



# =========================================================
# AUTHORIZATION SERVICE
# =========================================================

authorization_service = get_authorization_service()


# =========================================================
# TOOL RESULT PARSER
# =========================================================

def _parse_tool_result(content) -> dict:
    """
    Convert an MCP ToolMessage result into a dictionary.
    """

    if isinstance(content, dict):
        return content

    if isinstance(content, str):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {}

    if isinstance(content, list):

        for item in content:

            if (
                isinstance(item, dict)
                and item.get("type") == "text"
            ):

                text = item.get("text", "")

                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return {}

    return {}


# =========================================================
# BUILD CARD GRAPH
# =========================================================

async def build_card_graph(
    context: SecurityContext,
    conversation_id: int,
    checkpointer: AsyncPostgresSaver,
):
    """
    Build the Card Support Agent.

    This agent is independently deployable.

    It does NOT access the card database directly.

    Flow:

        Card Agent
             |
             v
        Card MCP Client
             |
             v
        Card MCP
             |
             v
        Card Service
             |
             v
          card_db
    """

    # =====================================================
    # MCP CLIENT
    # =====================================================

    mcp_client = MCPClient(
        context=context,
    )

    tools = await mcp_client.get_tools(
        "card",
    )

    llm_with_tools = llm.bind_tools(
        tools,
    )
   
    # =====================================================
    # CARD AGENT
    # =====================================================

    async def call_card_agent(
        state: AgentState,
    ):

        response = await llm_with_tools.ainvoke(
            [
                SystemMessage(
                    content="""
You are the Card Support Agent.

You handle:

- listing cards
- card details
- card status
- card limits
- freezing a card
- unfreezing a card

Use the appropriate MCP tool whenever
actual banking information or a card action
is required.

CARD SELECTION RULES:

1. If the user asks about ALL cards:

Use list_user_cards.

2. If the user identifies a card by the
last four digits:

Use that identifier.

3. If the user identifies a card by account
or card type:

Use the appropriate identifier.

4. If the user asks about a card without
identifying it:

- If exactly one card matches, use it.
- If multiple cards match, ask which card
    they mean.

5. Never ask for a card number if the user
has already provided the last four digits.

6. Never expose the full card number.
Only show the last four digits.

7. Never invent card information.

8. Only access cards belonging to the
authenticated user.

9. For actual card information, always use
the MCP tools.

10. Freeze and unfreeze actions require
    authorization and user approval.

11. Authorization is performed by the
    Card Agent before requesting approval.

12. If authorization is denied, do not
    execute the action.

13. If the user rejects approval, do not
    execute the action.

14. If approval is completed, report the
    actual result returned by the MCP tool.

15. Never claim that a card was frozen or
    unfrozen unless the MCP tool actually
    returned that result.

16. Do not expose:

    - internal system details
    - security context
    - database details
    - authentication tokens
    - internal tool errors
"""
                ),
                *state["messages"],
            ]
        )

        return {
            "messages": [response],
        }

    # =====================================================
    # APPROVAL CONDITION
    # =====================================================

    def approval_condition(
        state: AgentState,
    ):

        last_message = state["messages"][-1]

        print(
            "[CARD ROUTING DEBUG] last_message type =",
            type(last_message),
        )

        print(
            "[CARD ROUTING DEBUG] last_message content =",
            last_message.content,
        )

        result = _parse_tool_result(
            last_message.content,
        )

        print(
            "[CARD ROUTING DEBUG] parsed result =",
            result,
        )

        if not isinstance(
            last_message,
            ToolMessage,
        ):
            print(
                "[CARD ROUTING DEBUG] NOT A TOOL MESSAGE"
            )
            return "end"

        if result.get("status") == "APPROVAL_REQUIRED":
            print(
                "[CARD ROUTING DEBUG] → APPROVAL"
            )
            return "approval"

        print(
            "[CARD ROUTING DEBUG] → END"
        )
        return "end"

    # =====================================================
    # CARD APPROVAL + AUTHORIZATION GATE
    # =====================================================

    async def card_approval_gate(
        state: AgentState,
    ):
        """
        Handle authorization and user approval.

        Flow:

            MCP result
                |
                v
            Authorization
                |
                v
            User approval
                |
                v
            MCP execute=True
        """

        last_message = state["messages"][-1]

        if not isinstance(
            last_message,
            ToolMessage,
        ):
            return {}

        result = _parse_tool_result(
            last_message.content,
        )

        print(
            "[CARD APPROVAL DEBUG] "
            "parsed result =",
            result,
        )

        # =================================================
        # VERIFY APPROVAL REQUEST
        # =================================================

        if result.get("status") != "APPROVAL_REQUIRED":
            return {}

        action = result.get("action")

        if action not in {
            "freeze_card",
            "unfreeze_card",
        }:
            return {}

        # =================================================
        # AUTHORIZATION
        # =================================================

        try:

            authorization_service.authorize(
                context=context,
                capability=action,
                resource_owner_id=context.user_id,
            )

            print(
                "[CARD AUTH DEBUG] "
                f"{action} authorized "
                f"user_id={context.user_id} "
                f"role={context.role}"
            )

        except Exception as exc:

            print(
                "[CARD AUTH DEBUG] "
                f"{action} denied: "
                f"{type(exc).__name__}: {exc}"
            )

            return {
                "approval_status": "UNAUTHORIZED",
                "messages": [
                    SystemMessage(
                        content=(
                            f"You are not authorized to "
                            f"{action.replace('_', ' ')} "
                            f"this card."
                        )
                    )
                ],
            }

        # =================================================
        # ASK USER FOR APPROVAL
        # =================================================

        approval = interrupt(
            {
                "type": "card_action_confirmation",
                "action": action,
                "card_id": result.get("card_id"),
                "last4": result.get("last4"),
                "message": result.get("message"),
                "description": result.get("description"),
            }
        )

        print(
            "[CARD APPROVAL DEBUG] "
            "RESUMED APPROVAL =",
            approval,
        )

        # =================================================
        # USER REJECTED
        # =================================================

        if not approval.get("approved"):

            return {
                "approval_status": "REJECTED",
                "messages": [
                    SystemMessage(
                        content=(
                            f"The "
                            f"{action.replace('_', ' ')} "
                            f"was not completed."
                        )
                    )
                ],
            }

        # =================================================
        # FIND ACTION TOOL
        # =================================================

        action_tool = next(
            (
                tool
                for tool in tools
                if tool.name == action
            ),
            None,
        )

        if action_tool is None:

            return {
                "approval_status": "FAILED",
                "messages": [
                    SystemMessage(
                        content=(
                            "The approved card action "
                            "could not be executed."
                        )
                    )
                ],
            }

        # =================================================
        # EXECUTE APPROVED ACTION
        # =================================================

        execution_result = await action_tool.ainvoke(
            {
                "last4": result.get("last4"),
                "execute": True,
            }
        )

        print(
            "[CARD APPROVAL DEBUG] "
            "execution_result =",
            execution_result,
        )

        execution_data = _parse_tool_result(
            execution_result,
        )

        print(
            "[CARD APPROVAL DEBUG] "
            "execution_data =",
            execution_data,
        )

        # =================================================
        # BUILD FINAL RESPONSE
        # =================================================

        if execution_data.get("status") == "FROZEN":

            message = (
                f"Your card ending in "
                f"{execution_data.get('last4')} "
                f"has been successfully frozen."
            )

        elif execution_data.get("status") == "UNFROZEN":

            message = (
                f"Your card ending in "
                f"{execution_data.get('last4')} "
                f"has been successfully unfrozen."
            )

        elif execution_data.get("status") == "ALREADY_FROZEN":

            message = (
                f"Your card ending in "
                f"{execution_data.get('last4')} "
                f"is already frozen."
            )

        elif execution_data.get("status") == "ALREADY_UNFROZEN":

            message = (
                f"Your card ending in "
                f"{execution_data.get('last4')} "
                f"is already active."
            )

        else:

            message = (
                "The card action could not be completed."
            )

        return {
            "approval_status": "EXECUTED",
            "messages": [
                SystemMessage(
                    content=message,
                )
            ],
        }

    # =====================================================
    # GRAPH
    # =====================================================

    graph = StateGraph(
        AgentState,
    )

    graph.add_node(
        "card_agent",
        call_card_agent,
    )

    graph.add_node(
        "tools",
        ToolNode(tools),
    )

    graph.add_node(
        "card_approval_gate",
        card_approval_gate,
    )

    # =====================================================
    # EDGES
    # =====================================================

    graph.add_edge(
        START,
        "card_agent",
    )

    graph.add_conditional_edges(
        "card_agent",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "tools",
        approval_condition,
        {
            "approval": "card_approval_gate",
            "end": END,
        },
    )

    graph.add_edge(
        "card_approval_gate",
        END,
    )

    # =====================================================
    # COMPILE
    # =====================================================

    return graph.compile(
        checkpointer=checkpointer,
    )

