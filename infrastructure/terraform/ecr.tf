locals {
  ecr_repositories = {
    main_backend        = "banking-main"
    account_agent       = "banking-account-agent"
    account_mcp         = "banking-account-mcp"
    account_service     = "banking-account-service"
    transaction_agent   = "banking-transaction-agent"
    transaction_mcp     = "banking-transaction-mcp"
    transaction_service = "banking-transaction-service"
    card_agent          = "banking-card-agent"
    card_mcp            = "banking-card-mcp"
    card_service        = "banking-card-service"
    rag_agent           = "banking-rag-agent"
    rag_mcp             = "banking-rag-mcp"
    rag_service         = "banking-rag-service"
    otel_collector      = "banking-otel-collector"
  }
}

resource "aws_ecr_repository" "services" {
  for_each = local.ecr_repositories

  name                 = each.value
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}