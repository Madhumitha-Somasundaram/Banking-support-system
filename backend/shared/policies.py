"""
Role-Based Access Control (RBAC) Policies.

Defines what each role can and cannot do in the system.

Roles:
  - CUSTOMER: End user with access to their own accounts
  - SUPPORT_AGENT: Support staff can view accounts (with audit logging)
  - ADMIN: Full system access
"""

ROLE_CAPABILITIES = {
    "CUSTOMER": {
        # Read operations
        "get_balance",
        "get_account_details",
        "get_account_status",
        "get_card_status",
        "get_transaction_history",
        "get_transaction_details",
        "get_payment_status",
        "freeze_card",
        "unfreeze_card",
        # Write operations (may require approval)
        "make_payment",
        "transfer_money",
        "activate_card",
        "request_card_replacement",
        "set_spending_limits",
        "enable_international_transactions",

        # Account operations
        "view_conversation_history",
        "create_conversation",
    },

    "SUPPORT_AGENT": {
        # Read operations (audit logged)
        "get_balance",
        "get_account_details",
        "get_account_status",
        "get_card_status",
        "get_transaction_history",
        "get_transaction_details",
        "view_customer_conversations",

        # Support operations
        "add_support_note",
        "escalate_issue",
        "view_audit_logs",
    },

    "ADMIN": {
        # All capabilities
        # Read
        "get_balance",
        "get_account_details",
        "get_account_status",
        "get_card_status",
        "get_transaction_history",
        "get_transaction_details",
        "get_payment_status",
        "view_all_accounts",
        "view_all_transactions",
        "view_all_conversations",
        "view_audit_logs",

        # Write
        "make_payment",
        "transfer_money",
        "activate_card",
        "freeze_card",
        "close_account",
        "set_spending_limits",
        "enable_international_transactions",

        # Admin operations
        "approve_critical_task",
        "reject_critical_task",
        "create_user",
        "update_user_role",
        "view_system_metrics",
        "manage_system_config",
    },
}

# Resource ownership model
# CUSTOMER can only access their own resources
# ADMIN can access any resource
# SUPPORT_AGENT can access customer resources (with audit logging)

RESOURCE_OWNERSHIP_MODEL = {
    "account": {
        "CUSTOMER": "own",  # Can only access own accounts
        "SUPPORT_AGENT": "view_with_audit",  # Can view with logging
        "ADMIN": "all",  # Can access any account
    },
    "conversation": {
        "CUSTOMER": "own",
        "SUPPORT_AGENT": "view_with_audit",
        "ADMIN": "all",
    },
    "transaction": {
        "CUSTOMER": "own",
        "SUPPORT_AGENT": "view_with_audit",
        "ADMIN": "all",
    },
    "user": {
        "CUSTOMER": "own",
        "SUPPORT_AGENT": "limited",
        "ADMIN": "all",
    },
}

# Audit logging requirements
AUDIT_REQUIRED_OPERATIONS = {
    "make_payment",
    "transfer_money",
    "freeze_card",
    "close_account",
    "set_spending_limits",
    "approve_critical_task",
    "reject_critical_task",
}