"""
Transaction MCP Server

Exposes transaction operations as tools for LLMs via Model Context Protocol.
Communicates with Transaction Service via HTTP.

Architecture:
  MCP Server (this) :8002
      ↓ HTTP
  Transaction Service :8102
      ↓
  transaction_db
"""

from mcp.server.fastmcp import Context, FastMCP
import httpx

from shared.context import SecurityContext
from shared.internal_token import verify_internal_token
from shared.config import settings

mcp = FastMCP(
    "TransactionServer",
    host="0.0.0.0",
    port=8002,
)


# =========================================================
# SECURITY: Token Validation & Context Extraction
# =========================================================

def get_security_context(ctx: Context) -> SecurityContext:
    """Extract and validate security context from MCP request."""
    request = ctx.request_context.request

    if request is None:
        raise ValueError("MCP request context is unavailable")

    authorization = request.headers.get("Authorization")

    if not authorization:
        raise ValueError("Authentication required")

    if not authorization.startswith("Bearer "):
        raise ValueError("Invalid authentication scheme")

    token = authorization.removeprefix("Bearer ").strip()

    try:
        payload = verify_internal_token(token)
    except Exception as exc:
        raise ValueError("Invalid internal authentication") from exc

    return SecurityContext(
        user_id=int(payload["sub"]),
        role=payload["role"],
    )


# =========================================================
# HTTP CLIENT TO TRANSACTION SERVICE
# =========================================================

def call_transaction_service(
    endpoint: str,
    user_id: int,
    params: dict | None = None,
) -> dict:
    """Call the Transaction Service HTTP API."""
    url = f"{settings.TRANSACTION_SERVICE_URL}{endpoint}"

    query_params = {"user_id": user_id}
    if params:
        query_params.update(params)

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=query_params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise ValueError(f"Transaction Service error: {str(exc)}") from exc


# =========================================================
# TOOL 1: LIST USER TRANSACTIONS
# =========================================================

@mcp.tool()
def list_user_transactions(
    ctx: Context,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """
    List all transactions for user's accounts.

    Parameters:
        limit: Maximum results (default 50)
        offset: Result offset (default 0)

    Returns:
        {
            "status": str,
            "transactions": [
                {
                    "transaction_id": int,
                    "reference_number": str,
                    "from_account_id": int | None,
                    "to_account_id": int | None,
                    "transaction_type": str,
                    "amount": float,
                    "status": str,
                    "direction": str (INCOMING, OUTGOING, UNKNOWN),
                    "description": str | None,
                    "merchant_name": str | None,
                    "transaction_date": str (ISO),
                    "dispute_status": str
                }
            ]
        }
    """
    context = get_security_context(ctx)
    return call_transaction_service(
        endpoint="/transactions/",
        user_id=context.user_id,
        params={"limit": limit, "offset": offset},
    )


# =========================================================
# TOOL 2: GET TRANSACTION BY ID
# =========================================================

@mcp.tool()
def get_transaction(
    ctx: Context,
    transaction_id: int,
) -> dict:
    """
    Get a specific transaction (with authorization check).

    Parameters:
        transaction_id: Transaction ID

    Returns:
        Transaction details (same format as list_user_transactions)
    """
    context = get_security_context(ctx)
    return call_transaction_service(
        endpoint=f"/transactions/{transaction_id}",
        user_id=context.user_id,
    )


# =========================================================
# TOOL 3: GET TRANSACTION BY REFERENCE
# =========================================================

@mcp.tool()
def get_transaction_by_reference(
    ctx: Context,
    reference_number: str,
) -> dict:
    """
    Get transaction by reference number (with authorization check).

    Parameters:
        reference_number: Transaction reference number

    Returns:
        Transaction details (same format as list_user_transactions)
    """
    context = get_security_context(ctx)
    return call_transaction_service(
        endpoint=f"/transactions/reference/{reference_number}",
        user_id=context.user_id,
    )


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
