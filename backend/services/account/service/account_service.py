"""Account Service - Business logic layer for Account domain."""

from enum import Enum

from sqlalchemy.orm import Session

from services.account.repository.account_repository import AccountRepository


class AccountResolutionStatus(str, Enum):
    """Account resolution result status."""
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    INVALID = "INVALID"


class AccountService:
    """Business logic for account operations."""

    def __init__(self):
        self.repository = AccountRepository()

    # ==================================================
    # ACCOUNT RESOLUTION
    # ==================================================

    def resolve_account(
        self,
        db: Session,
        user_id: int,
        account_number: str | None = None,
        last4: str | None = None,
        account_type: str | None = None,
    ) -> dict:
        """
        Resolve a single account from optional identifiers.

        Returns:
            {
                "status": AccountResolutionStatus,
                "account": Account | None,
                "matches": [...] (if AMBIGUOUS)
            }
        """
        # Validate last4
        if last4 is not None:
            if len(last4) != 4 or not last4.isdigit():
                return {
                    "status": AccountResolutionStatus.INVALID,
                    "account": None,
                }

        account_type_id = None

        # Resolve account type if provided
        if account_type:
            account_type_obj = (
                self.repository.get_account_type_by_name(
                    db=db,
                    name=account_type,
                )
            )

            if not account_type_obj:
                return {
                    "status": AccountResolutionStatus.NOT_FOUND,
                    "account": None,
                }

            account_type_id = account_type_obj.id

        # Dynamic account query
        accounts = self.repository.find_accounts(
            db=db,
            user_id=user_id,
            account_number=account_number,
            last4=last4,
            account_type_id=account_type_id,
        )

        if len(accounts) == 0:
            return {
                "status": AccountResolutionStatus.NOT_FOUND,
                "account": None,
            }

        if len(accounts) > 1:
            return {
                "status": AccountResolutionStatus.AMBIGUOUS,
                "account": None,
                "matches": [
                    {
                        "account_id": account.id,
                        "account_type_id": account.account_type_id,
                        "last4": account.account_number[-4:],
                        "status": account.status,
                    }
                    for account in accounts
                ],
            }

        return {
            "status": AccountResolutionStatus.FOUND,
            "account": accounts[0],
        }

    # ==================================================
    # LIST ACCOUNTS
    # ==================================================

    def list_accounts(
        self,
        db: Session,
        user_id: int,
    ) -> list[dict]:
        """Get all accounts for a user."""
        accounts = self.repository.find_accounts(
            db=db,
            user_id=user_id,
        )

        results = []

        for account in accounts:
            account_type = (
                self.repository.get_account_type_by_id(
                    db=db,
                    account_type_id=account.account_type_id,
                )
            )

            results.append({
                "account_id": account.id,
                "account_type": (
                    account_type.name
                    if account_type
                    else None
                ),
                "last4": account.account_number[-4:],
                "balance": float(account.balance),
                "status": account.status,
                "opened_date": (
                    account.opened_date.isoformat()
                    if account.opened_date
                    else None
                ),
            })

        return results

    # ==================================================
    # BALANCE
    # ==================================================

    def get_balance(
        self,
        db: Session,
        user_id: int,
        account_number: str | None = None,
        last4: str | None = None,
        account_type: str | None = None,
    ) -> dict:
        """Get account balance."""
        result = self.resolve_account(
            db=db,
            user_id=user_id,
            account_number=account_number,
            last4=last4,
            account_type=account_type,
        )

        if result["status"] != AccountResolutionStatus.FOUND:
            return {
                "status": result["status"],
                "message": self._resolution_message(result),
                "matches": result.get("matches", []),
            }

        account = result["account"]

        return {
            "status": "FOUND",
            "account_id": account.id,
            "account_type_id": account.account_type_id,
            "last4": account.account_number[-4:],
            "balance": float(account.balance),
            "account_status": account.status,
        }

    # ==================================================
    # DETAILS
    # ==================================================

    def get_details(
        self,
        db: Session,
        user_id: int,
        account_number: str | None = None,
        last4: str | None = None,
        account_type: str | None = None,
    ) -> dict:
        """Get account details."""
        result = self.resolve_account(
            db=db,
            user_id=user_id,
            account_number=account_number,
            last4=last4,
            account_type=account_type,
        )

        if result["status"] != AccountResolutionStatus.FOUND:
            return {
                "status": result["status"],
                "message": self._resolution_message(result),
                "matches": result.get("matches", []),
            }

        account = result["account"]

        account_type_obj = (
            self.repository.get_account_type_by_id(
                db=db,
                account_type_id=account.account_type_id,
            )
        )

        return {
            "status": "FOUND",
            "account_id": account.id,
            "account_type": (
                account_type_obj.name
                if account_type_obj
                else None
            ),
            "last4": account.account_number[-4:],
            "balance": float(account.balance),
            "account_status": account.status,
            "opened_date": (
                account.opened_date.isoformat()
                if account.opened_date
                else None
            ),
        }

    # ==================================================
    # STATUS
    # ==================================================

    def get_status(
        self,
        db: Session,
        user_id: int,
        account_number: str | None = None,
        last4: str | None = None,
        account_type: str | None = None,
    ) -> dict:
        """Get account status."""
        result = self.resolve_account(
            db=db,
            user_id=user_id,
            account_number=account_number,
            last4=last4,
            account_type=account_type,
        )

        if result["status"] != AccountResolutionStatus.FOUND:
            return {
                "status": result["status"],
                "message": self._resolution_message(result),
                "matches": result.get("matches", []),
            }

        account = result["account"]

        return {
            "status": "FOUND",
            "account_id": account.id,
            "account_type_id": account.account_type_id,
            "last4": account.account_number[-4:],
            "account_status": account.status,
        }

    # ==================================================
    # LIMITS
    # ==================================================

    def get_limits(
        self,
        db: Session,
        user_id: int,
        account_number: str | None = None,
        last4: str | None = None,
        account_type: str | None = None,
    ) -> dict:
        """Get account transaction limits."""
        result = self.resolve_account(
            db=db,
            user_id=user_id,
            account_number=account_number,
            last4=last4,
            account_type=account_type,
        )

        if result["status"] != AccountResolutionStatus.FOUND:
            return {
                "status": result["status"],
                "message": self._resolution_message(result),
                "matches": result.get("matches", []),
            }

        account = result["account"]

        account_type_obj = (
            self.repository.get_account_type_by_id(
                db=db,
                account_type_id=account.account_type_id,
            )
        )

        if not account_type_obj:
            return {
                "status": "ERROR",
                "message": "Account type configuration not found.",
            }

        return {
            "status": "FOUND",
            "account_id": account.id,
            "account_type": account_type_obj.name,
            "last4": account.account_number[-4:],
            "daily_transfer_limit": float(
                account_type_obj.daily_transfer_limit
            ),
            "daily_withdrawal_limit": float(
                account_type_obj.daily_withdrawal_limit
            ),
            "monthly_transfer_limit": float(
                account_type_obj.monthly_transfer_limit
            ),
        }

    # ==================================================
    # HELPER
    # ==================================================

    @staticmethod
    def _resolution_message(result: dict) -> str:
        """Generate user-friendly message for resolution result."""
        status = result["status"]

        if status == AccountResolutionStatus.INVALID:
            return "Invalid account identifier."

        if status == AccountResolutionStatus.NOT_FOUND:
            return "Account not found."

        if status == AccountResolutionStatus.AMBIGUOUS:
            return "Multiple accounts match the provided identifier."

        return "Unable to resolve account."
