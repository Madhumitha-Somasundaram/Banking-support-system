"""Account Repository - Data access layer for Account domain."""

from sqlalchemy.orm import Session

from services.account.models.account import Account, AccountType


class AccountRepository:
    """Account data access."""

    # ==================================================
    # ACCOUNT QUERIES
    # ==================================================

    def find_accounts(
        self,
        db: Session,
        user_id: int,
        account_number: str | None = None,
        last4: str | None = None,
        account_type_id: int | None = None,
    ) -> list[Account]:
        """
        Find accounts for a user with optional filters.

        Args:
            db: Database session
            user_id: User ID (authorization filter)
            account_number: Exact account number
            last4: Last 4 digits of account number
            account_type_id: Account type ID

        Returns:
            List of Account objects
        """
        query = db.query(Account).filter(Account.user_id == user_id)

        if account_number:
            query = query.filter(Account.account_number == account_number)

        if last4:
            query = query.filter(Account.account_number.endswith(last4))

        if account_type_id:
            query = query.filter(Account.account_type_id == account_type_id)

        return query.all()

    # ==================================================
    # ACCOUNT TYPE QUERIES
    # ==================================================

    def get_account_type_by_id(
        self,
        db: Session,
        account_type_id: int,
    ) -> AccountType | None:
        """Get account type by ID."""
        return (
            db.query(AccountType)
            .filter(AccountType.id == account_type_id)
            .first()
        )

    def get_account_type_by_name(
        self,
        db: Session,
        name: str,
    ) -> AccountType | None:
        """Get account type by name (case-insensitive)."""
        return (
            db.query(AccountType)
            .filter(AccountType.name == name.upper())
            .first()
        )

    def get_all_account_types(
        self,
        db: Session,
    ) -> list[AccountType]:
        """Get all account types."""
        return db.query(AccountType).all()
