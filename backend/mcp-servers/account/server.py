"""
Account MCP Server

This MCP server exposes account operations as tools for LLMs.
It communicates with the Account Service via HTTP (does NOT connect directly to database).

Architecture:
  MCP Server (this) :8001
      ↓ HTTP
  Account Service :8101
      ↓
  account_db
"""

from mcp.server.fastmcp import Context, FastMCP
import httpx

from shared.context import SecurityContext
from shared.internal_token import verify_internal_token
from shared.config import settings


mcp = FastMCP(
    "AccountServer",
    host="0.0.0.0",
    port=8001,
)


# =========================================================
# SECURITY: Token Validation & Context Extraction
# =========================================================

def get_security_context(ctx: Context) -> SecurityContext:
    """
    Extract and validate security context from MCP request.

    Flow:
    1. Get HTTP request from MCP context
    2. Extract Authorization header
    3. Verify Bearer token format
    4. Decode JWT (internal token)
    5. Return SecurityContext with user_id and role

    Raises:
        ValueError: If authentication fails at any step

    Returns:
        SecurityContext: Contains user_id and role
    """
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
# HTTP CLIENT TO ACCOUNT SERVICE
# =========================================================

def call_account_service(
    endpoint: str,
    user_id: int,
    params: dict | None = None,
) -> dict:
    """
    Call the Account Service HTTP API.

    Args:
        endpoint: API endpoint (e.g., "/accounts/", "/accounts/balance")
        user_id: User ID (required in query)
        params: Additional query parameters

    Returns:
        Response from Account Service

    Raises:
        httpx.HTTPError: If Account Service is unavailable
    """
    url = f"{settings.ACCOUNT_SERVICE_URL}{endpoint}"

    query_params = {"user_id": user_id}
    print("in account service",query_params,params)
    if params:
        query_params.update(params)

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, params=query_params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        raise ValueError(f"Account Service error: {str(exc)}") from exc


# =========================================================
# TOOL 1: LIST USER ACCOUNTS
# =========================================================

@mcp.tool()
def list_user_accounts(ctx: Context) -> list[dict]:
    """
    Get all accounts owned by the authenticated user.

    Returns:
        List of account dictionaries containing:
        - account_id: Account ID
        - account_type: Type (checking, savings, etc)
        - last4: Last 4 digits of account number
        - balance: Current balance
        - status: Account status (active, frozen, closed)
        - opened_date: Account opening date (ISO format)
    """
    context = get_security_context(ctx)
    return call_account_service(
        endpoint="/accounts/",
        user_id=context.user_id,
    )


# =========================================================
# TOOL 2: GET ACCOUNT BALANCE
# =========================================================

@mcp.tool()
def get_account_balance(
    ctx: Context,
    account_number: str | None = None,
    last4: str | None = None,
    account_type: str | None = None,
) -> dict:
    """
    Get balance for a user's account.

    Account Resolution:
    1. If account_number provided: Use exact match
    2. Else if last4 provided: Match last 4 digits
    3. Else if account_type provided: Use type
    4. Else if user has 1 account: Use default
    5. Else: Ask user which account

    Parameters:
        account_number: Full account number (e.g. "1234567890")
        last4: Last 4 digits (e.g. "7890")
        account_type: Account type (e.g. "checking")

    Returns:
        {
            "status": str,
            "account_id": int,
            "account_type_id": int,
            "last4": str,
            "balance": float,
            "account_status": str,
            "message": str (if not found),
            "matches": [...] (if ambiguous)
        }
    """
    context = get_security_context(ctx)
    print("in mcp tool account balance", context)
    params = {}
    if account_number:
        params["account_number"] = account_number
    if last4:
        params["last4"] = last4
    if account_type:
        params["account_type"] = account_type

    return call_account_service(
        endpoint="/accounts/balance",
        user_id=context.user_id,
        params=params,
    )


# =========================================================
# TOOL 3: GET ACCOUNT DETAILS
# =========================================================

@mcp.tool()
def get_account_details(
    ctx: Context,
    account_number: str | None = None,
    last4: str | None = None,
    account_type: str | None = None,
) -> dict:
    """
    Get detailed information about a user's account.

    Account Resolution:
    Same logic as get_account_balance

    Parameters:
        account_number: Full account number
        last4: Last 4 digits
        account_type: Account type

    Returns:
        {
            "status": str,
            "account_id": int,
            "account_type": str,
            "last4": str,
            "balance": float,
            "account_status": str,
            "opened_date": str (ISO),
            "message": str (if not found),
            "matches": [...] (if ambiguous)
        }
    """
    context = get_security_context(ctx)

    params = {}
    if account_number:
        params["account_number"] = account_number
    if last4:
        params["last4"] = last4
    if account_type:
        params["account_type"] = account_type

    return call_account_service(
        endpoint="/accounts/details",
        user_id=context.user_id,
        params=params,
    )


# =========================================================
# TOOL 4: GET ACCOUNT STATUS
# =========================================================

@mcp.tool()
def get_account_status(
    ctx: Context,
    account_number: str | None = None,
    last4: str | None = None,
    account_type: str | None = None,
) -> dict:
    """
    Check the status of a user's account.

    Account Resolution:
    Same logic as get_account_balance

    Parameters:
        account_number: Full account number
        last4: Last 4 digits
        account_type: Account type

    Returns:
        {
            "status": str,
            "account_id": int,
            "account_type_id": int,
            "last4": str,
            "account_status": str,
            "message": str (if not found),
            "matches": [...] (if ambiguous)
        }
    """
    context = get_security_context(ctx)

    params = {}
    if account_number:
        params["account_number"] = account_number
    if last4:
        params["last4"] = last4
    if account_type:
        params["account_type"] = account_type

    return call_account_service(
        endpoint="/accounts/status",
        user_id=context.user_id,
        params=params,
    )


# =========================================================
# TOOL 5: GET ACCOUNT LIMITS
# =========================================================

@mcp.tool()
def get_account_limits(
    ctx: Context,
    account_number: str | None = None,
    last4: str | None = None,
    account_type: str | None = None,
) -> dict:
    """
    Get transaction limits for a user's account.

    Account Resolution:
    Same logic as get_account_balance

    Parameters:
        account_number: Full account number
        last4: Last 4 digits
        account_type: Account type

    Returns:
        {
            "status": str,
            "account_id": int,
            "account_type": str,
            "last4": str,
            "daily_transfer_limit": float,
            "daily_withdrawal_limit": float,
            "monthly_transfer_limit": float,
            "message": str (if not found),
            "matches": [...] (if ambiguous)
        }
    """
    context = get_security_context(ctx)

    params = {}
    if account_number:
        params["account_number"] = account_number
    if last4:
        params["last4"] = last4
    if account_type:
        params["account_type"] = account_type

    return call_account_service(
        endpoint="/accounts/limits",
        user_id=context.user_id,
        params=params,
    )


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
