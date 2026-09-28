
from mcp.server.fastmcp import Context, FastMCP
import httpx

from shared.context import SecurityContext
from shared.internal_token import verify_internal_token
from shared.config import settings


mcp = FastMCP(
    "CardServer",
    host="0.0.0.0",
    port=8003,
)


# =========================================================
# SECURITY
# =========================================================

def get_security_context(ctx: Context) -> SecurityContext:
    """
    Extract and validate the internal service token.
    """

    request = ctx.request_context.request

    if request is None:
        raise ValueError(
            "MCP request context is unavailable"
        )

    authorization = request.headers.get(
        "Authorization"
    )

    if not authorization:
        raise ValueError(
            "Authentication required"
        )

    if not authorization.startswith("Bearer "):
        raise ValueError(
            "Invalid authentication scheme"
        )

    token = authorization.removeprefix(
        "Bearer "
    ).strip()

    try:
        payload = verify_internal_token(token)

    except Exception as exc:
        raise ValueError(
            "Invalid internal authentication"
        ) from exc

    return SecurityContext(
        user_id=int(payload["sub"]),
        role=payload["role"],
        conversation_id=payload.get("conversation_id"),
    )


# =========================================================
# CARD SERVICE HTTP CLIENT
# =========================================================

def call_card_service(
    method: str,
    endpoint: str,
    user_id: int,
    params: dict | None = None,
) -> dict | list:
    """
    Call the Card Service REST API.

    The MCP server does not access card_db directly.
    """

    url = (
        f"{settings.CARD_SERVICE_URL}"
        f"{endpoint}"
    )

    query_params = {
        "user_id": user_id
    }
    print("[CARD DEUBUG]",query_params)
    if params:
        query_params.update(params)

    try:

        with httpx.Client(timeout=10.0) as client:

            response = client.request(
                method=method,
                url=url,
                params=query_params,
            )

            response.raise_for_status()

            return response.json()

    except httpx.HTTPStatusError as exc:

        try:
            detail = exc.response.json()
        except Exception:
            detail = exc.response.text

        raise ValueError(
            f"Card Service returned "
            f"{exc.response.status_code}: {detail}"
        ) from exc

    except httpx.HTTPError as exc:

        raise ValueError(
            f"Card Service unavailable: {str(exc)}"
        ) from exc


# =========================================================
# READ TOOLS
# =========================================================


@mcp.tool()
def list_user_cards(
    ctx: Context,
    account_id: int | None = None,
    status: str | None = None,
) -> list[dict]:
    """
    List all cards belonging to the authenticated user.

    Optional filters:
        account_id
        status
    """

    context = get_security_context(ctx)

    params = {}

    if account_id is not None:
        params["account_id"] = account_id

    if status is not None:
        params["status"] = status

    return call_card_service(
        method="GET",
        endpoint="/cards/",
        user_id=context.user_id,
        params=params,
    )


@mcp.tool()
def get_card_details(
    ctx: Context,
    card_number: str | None = None,
    last4: str | None = None,
    account_id: int | None = None,
    card_type: str | None = None,
) -> dict:
    """
    Get details for a card.

    If one card matches, return its details.

    If multiple cards match, return an ambiguous result.

    The full card number is never returned.
    """

    context = get_security_context(ctx)

    params = {}

    if card_number is not None:
        params["card_number"] = card_number

    if last4 is not None:
        params["last4"] = last4

    if account_id is not None:
        params["account_id"] = account_id

    if card_type is not None:
        params["card_type"] = card_type

    return call_card_service(
        method="GET",
        endpoint="/cards/details",
        user_id=context.user_id,
        params=params,
    )


@mcp.tool()
def get_card_status(
    ctx: Context,
    card_number: str | None = None,
    last4: str | None = None,
    account_id: int | None = None,
    card_type: str | None = None,
) -> dict:
    """
    Get the status of a card.
    """

    context = get_security_context(ctx)

    params = {}

    if card_number is not None:
        params["card_number"] = card_number

    if last4 is not None:
        params["last4"] = last4

    if account_id is not None:
        params["account_id"] = account_id

    if card_type is not None:
        params["card_type"] = card_type

    return call_card_service(
        method="GET",
        endpoint="/cards/status",
        user_id=context.user_id,
        params=params,
    )


@mcp.tool()
def get_card_limits(
    ctx: Context,
    card_number: str | None = None,
    last4: str | None = None,
    account_id: int | None = None,
    card_type: str | None = None,
) -> dict:
    """
    Get purchase and ATM limits for a card.
    """

    context = get_security_context(ctx)

    params = {}

    if card_number is not None:
        params["card_number"] = card_number

    if last4 is not None:
        params["last4"] = last4

    if account_id is not None:
        params["account_id"] = account_id

    if card_type is not None:
        params["card_type"] = card_type

    return call_card_service(
        method="GET",
        endpoint="/cards/limits",
        user_id=context.user_id,
        params=params,
    )


# =========================================================
# WRITE TOOLS
# =========================================================


@mcp.tool()
def freeze_card(
    ctx: Context,
    card_number: str | None = None,
    last4: str | None = None,
    execute: bool = False,
) -> dict:
    """
    Freeze a card.

    First call:
        execute=False

        Returns APPROVAL_REQUIRED.

    After the MCP client obtains user approval:
        execute=True

        Executes the freeze.

    Authorization/approval is handled by the MCP
    client/agent layer.
    """

    context = get_security_context(ctx)

    params = {
        "execute": execute
    }

    if card_number is not None:
        params["card_number"] = card_number

    if last4 is not None:
        params["last4"] = last4

    return call_card_service(
        method="POST",
        endpoint="/cards/freeze",
        user_id=context.user_id,
        params=params,
    )


@mcp.tool()
def unfreeze_card(
    ctx: Context,
    card_number: str | None = None,
    last4: str | None = None,
    execute: bool = False,
) -> dict:
    """
    Unfreeze a card.

    First call:
        execute=False

        Returns APPROVAL_REQUIRED.

    After the MCP client obtains user approval:
        execute=True

        Executes the unfreeze.

    Authorization/approval is handled by the MCP
    client/agent layer.
    """

    context = get_security_context(ctx)

    params = {
        "execute": execute
    }

    if card_number is not None:
        params["card_number"] = card_number

    if last4 is not None:
        params["last4"] = last4

    return call_card_service(
        method="POST",
        endpoint="/cards/unfreeze",
        user_id=context.user_id,
        params=params,
    )


# =========================================================
# SERVER START
# =========================================================

if __name__ == "__main__":

    mcp.run(
        transport="streamable-http"
    )