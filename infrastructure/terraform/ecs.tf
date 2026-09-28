resource "aws_ecs_cluster" "banking" {
  name = "banking-support"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# SERVICE DISCOVERY
# ============================================================

resource "aws_service_discovery_private_dns_namespace" "banking" {
  name        = "banking.local"
  description = "Private service discovery namespace for Banking Support"

  vpc = var.vpc_id

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# CLOUDWATCH
# ============================================================

resource "aws_cloudwatch_log_group" "banking" {
  name              = "/ecs/banking-support"
  retention_in_days = 7

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# COMMON ENVIRONMENT
# ============================================================

locals {

  common_environment = [

    # ========================================================
    # ACCOUNT
    # ========================================================

    {
      name  = "ACCOUNT_MCP_URL"
      value = "http://account-mcp:8001/mcp"
    },
    {
      name  = "ACCOUNT_SERVICE_URL"
      value = "http://account-service:8101"
    },
    {
      name  = "ACCOUNT_AGENT_URL"
      value = "http://account-agent:8201/invoke"
    },

    # ========================================================
    # TRANSACTION
    # ========================================================

    {
      name  = "TRANSACTION_MCP_URL"
      value = "http://transaction-mcp:8002/mcp"
    },
    {
      name  = "TRANSACTION_SERVICE_URL"
      value = "http://transaction-service:8102"
    },
    {
      name  = "TRANSACTION_AGENT_URL"
      value = "http://transaction-agent:8202/invoke"
    },

    # ========================================================
    # CARD
    # ========================================================

    {
      name  = "CARD_MCP_URL"
      value = "http://card-mcp:8003/mcp"
    },
    {
      name  = "CARD_SERVICE_URL"
      value = "http://card-service:8103"
    },
    {
      name  = "CARD_AGENT_URL"
      value = "http://card-agent:8203/invoke"
    },

    # ========================================================
    # RAG
    # ========================================================

    {
      name  = "RAG_MCP_URL"
      value = "http://rag-mcp:8004/mcp"
    },
    {
      name  = "RAG_SERVICE_URL"
      value = "http://rag-service:8104"
    },
    {
      name  = "RAG_AGENT_URL"
      value = "http://rag-agent:8204/invoke"
    },

    # ========================================================
    # OPENSEARCH / KNOWLEDGE
    # ========================================================

    {
      name  = "OPENSEARCH_URL"
      value = var.opensearch_url
    },
    {
      name  = "OPENSEARCH_INDEX"
      value = "banking-knowledge"
    },
    {
      name  = "KNOWLEDGE_S3_BUCKET"
      value = var.knowledge_s3_bucket
    },
    {
      name  = "KNOWLEDGE_S3_PREFIX"
      value = "knowledge"
    },

    # ========================================================
    # BEDROCK
    # ========================================================

    {
      name  = "BEDROCK_REGION"
      value = "us-east-1"
    },
    {
      name  = "BEDROCK_EMBEDDING_MODEL"
      value = var.bedrock_embedding_model
    },
    {
      name  = "AGENT_QUEUE_URL"
      value = aws_sqs_queue.agent_jobs.url
    },
    {
      name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
      value = "http://127.0.0.1:4317"
    }
  ]

  # ========================================================
  # COMMON SECRETS
  # ========================================================

  common_secrets = [
    {
      name      = "DATABASE_URL"
      valueFrom = "${aws_secretsmanager_secret.banking_app.arn}:DATABASE_URL::"
    },
    {
      name      = "ACCOUNT_DATABASE_URL"
      valueFrom = "${aws_secretsmanager_secret.banking_app.arn}:ACCOUNT_DATABASE_URL::"
    },
    {
      name      = "TRANSACTION_DATABASE_URL"
      valueFrom = "${aws_secretsmanager_secret.banking_app.arn}:TRANSACTION_DATABASE_URL::"
    },
    {
      name      = "CARD_DATABASE_URL"
      valueFrom = "${aws_secretsmanager_secret.banking_app.arn}:CARD_DATABASE_URL::"
    },
    {
      name      = "LANGGRAPH_CHECKPOINT_DATABASE_URL"
      valueFrom = "${aws_secretsmanager_secret.banking_app.arn}:LANGGRAPH_CHECKPOINT_DATABASE_URL::"
    },
    {
      name      = "JWT_SECRET_KEY"
      valueFrom = "${aws_secretsmanager_secret.banking_app.arn}:JWT_SECRET_KEY::"
    },
    {
      name      = "OPENAI_API_KEY"
      valueFrom = "${aws_secretsmanager_secret.banking_app.arn}:OPENAI_API_KEY::"
    }
  ]

  # ========================================================
  # NETWORK
  # ========================================================

  private_subnets = [
    "subnet-01203b30ee3e6c17e",
    "subnet-043b8b46e1a09b4d9"
  ]

  service_security_groups = [
    "sg-00a33b43eb2147281"
  ]
}

# ============================================================
# ACCOUNT SERVICE
# ============================================================

resource "aws_ecs_task_definition" "account_service" {

  family                   = "banking-account-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "account-service"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-account-service:latest"
      essential = true

      portMappings = [
        {
          name          = "account-service"
          containerPort = 8101
          hostPort      = 8101
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment

      secrets = local.common_secrets


      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "account-service"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "account_service" {

  name            = "account-service"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.account_service.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets         = local.private_subnets
    security_groups = local.service_security_groups

    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "account-service"
      discovery_name = "account-service"

      client_alias {
        dns_name = "account-service"
        port     = 8101
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# TRANSACTION SERVICE
# ============================================================

resource "aws_ecs_task_definition" "transaction_service" {

  family                   = "banking-transaction-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "transaction-service"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-transaction-service:latest"
      essential = true

      portMappings = [
        {
          name          = "transaction-service"
          containerPort = 8102
          hostPort      = 8102
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment

      secrets = local.common_secrets

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "transaction-service"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "transaction_service" {

  name            = "transaction-service"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.transaction_service.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets         = local.private_subnets
    security_groups = local.service_security_groups

    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "transaction-service"
      discovery_name = "transaction-service"

      client_alias {
        dns_name = "transaction-service"
        port     = 8102
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# CARD SERVICE
# ============================================================

resource "aws_ecs_task_definition" "card_service" {

  family                   = "banking-card-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "card-service"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-card-service:latest"
      essential = true

      portMappings = [
        {
          name          = "card-service"
          containerPort = 8103
          hostPort      = 8103
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment

      secrets = local.common_secrets

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "card-service"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "card_service" {

  name            = "card-service"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.card_service.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets         = local.private_subnets
    security_groups = local.service_security_groups

    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "card-service"
      discovery_name = "card-service"

      client_alias {
        dns_name = "card-service"
        port     = 8103
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# RAG SERVICE
# ============================================================

resource "aws_ecs_task_definition" "rag_service" {

  family                   = "banking-rag-service"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "rag-service"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-rag-service:latest"
      essential = true

      portMappings = [
        {
          name          = "rag-service"
          containerPort = 8104
          hostPort      = 8104
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment
      secrets     = local.common_secrets

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "rag-service"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "rag_service" {

  name            = "rag-service"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.rag_service.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets         = local.private_subnets
    security_groups = local.service_security_groups

    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "rag-service"
      discovery_name = "rag-service"

      client_alias {
        dns_name = "rag-service"
        port     = 8104
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# ============================================================
# ACCOUNT MCP
# ============================================================
# ============================================================

resource "aws_ecs_task_definition" "account_mcp" {

  family                   = "banking-account-mcp"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "account-mcp"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-account-mcp:latest"
      essential = true

      portMappings = [
        {
          name          = "account-mcp"
          containerPort = 8001
          hostPort      = 8001
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment
      secrets     = local.common_secrets

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "account-mcp"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "account_mcp" {

  name            = "account-mcp"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.account_mcp.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets         = local.private_subnets
    security_groups = local.service_security_groups

    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "account-mcp"
      discovery_name = "account-mcp"

      client_alias {
        dns_name = "account-mcp"
        port     = 8001
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# TRANSACTION MCP
# ============================================================

resource "aws_ecs_task_definition" "transaction_mcp" {

  family                   = "banking-transaction-mcp"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "transaction-mcp"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-transaction-mcp:latest"
      essential = true

      portMappings = [
        {
          name          = "transaction-mcp"
          containerPort = 8002
          hostPort      = 8002
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment
      secrets     = local.common_secrets

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "transaction-mcp"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "transaction_mcp" {

  name            = "transaction-mcp"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.transaction_mcp.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets         = local.private_subnets
    security_groups = local.service_security_groups

    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "transaction-mcp"
      discovery_name = "transaction-mcp"

      client_alias {
        dns_name = "transaction-mcp"
        port     = 8002
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# CARD MCP
# ============================================================

resource "aws_ecs_task_definition" "card_mcp" {

  family                   = "banking-card-mcp"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "card-mcp"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-card-mcp:latest"
      essential = true

      portMappings = [
        {
          name          = "card-mcp"
          containerPort = 8003
          hostPort      = 8003
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment
      secrets     = local.common_secrets

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "card-mcp"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "card_mcp" {

  name            = "card-mcp"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.card_mcp.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets         = local.private_subnets
    security_groups = local.service_security_groups

    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "card-mcp"
      discovery_name = "card-mcp"

      client_alias {
        dns_name = "card-mcp"
        port     = 8003
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# RAG MCP
# ============================================================

resource "aws_ecs_task_definition" "rag_mcp" {

  family                   = "banking-rag-mcp"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "rag-mcp"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-rag-mcp:latest"
      essential = true

      portMappings = [
        {
          name          = "rag-mcp"
          containerPort = 8004
          hostPort      = 8004
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment
      secrets     = local.common_secrets

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "rag-mcp"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "rag_mcp" {

  name            = "rag-mcp"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.rag_mcp.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets         = local.private_subnets
    security_groups = local.service_security_groups

    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "rag-mcp"
      discovery_name = "rag-mcp"

      client_alias {
        dns_name = "rag-mcp"
        port     = 8004
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# ACCOUNT AGENT
# ============================================================

resource "aws_ecs_task_definition" "account_agent" {

  family                   = "banking-account-agent"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "account-agent"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-account-agent:latest"
      essential = true

      portMappings = [
        {
          name          = "account-agent"
          containerPort = 8201
          hostPort      = 8201
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment
      secrets     = local.common_secrets

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "account-agent"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "account_agent" {

  name            = "account-agent"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.account_agent.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets         = local.private_subnets
    security_groups = local.service_security_groups

    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "account-agent"
      discovery_name = "account-agent"

      client_alias {
        dns_name = "account-agent"
        port     = 8201
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# TRANSACTION AGENT
# ============================================================

resource "aws_ecs_task_definition" "transaction_agent" {

  family                   = "banking-transaction-agent"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "transaction-agent"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-transaction-agent:latest"
      essential = true

      portMappings = [
        {
          name          = "transaction-agent"
          containerPort = 8202
          hostPort      = 8202
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment
      secrets     = local.common_secrets

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "transaction-agent"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "transaction_agent" {

  name            = "transaction-agent"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.transaction_agent.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets         = local.private_subnets
    security_groups = local.service_security_groups

    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "transaction-agent"
      discovery_name = "transaction-agent"

      client_alias {
        dns_name = "transaction-agent"
        port     = 8202
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# CARD AGENT
# ============================================================

resource "aws_ecs_task_definition" "card_agent" {

  family                   = "banking-card-agent"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "card-agent"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-card-agent:latest"
      essential = true

      portMappings = [
        {
          name          = "card-agent"
          containerPort = 8203
          hostPort      = 8203
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment
      secrets     = local.common_secrets

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "card-agent"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "card_agent" {

  name            = "card-agent"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.card_agent.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets         = local.private_subnets
    security_groups = local.service_security_groups

    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "card-agent"
      discovery_name = "card-agent"

      client_alias {
        dns_name = "card-agent"
        port     = 8203
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ============================================================
# RAG AGENT
# ============================================================

resource "aws_ecs_task_definition" "rag_agent" {

  family                   = "banking-rag-agent"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "256"
  memory = "512"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "rag-agent"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-rag-agent:latest"
      essential = true

      portMappings = [
        {
          name          = "rag-agent"
          containerPort = 8204
          hostPort      = 8204
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment
      secrets     = local.common_secrets

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "rag-agent"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "rag_agent" {

  name            = "rag-agent"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.rag_agent.arn

  desired_count = 1
  launch_type   = "FARGATE"

  network_configuration {
    subnets         = local.private_subnets
    security_groups = local.service_security_groups

    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "rag-agent"
      discovery_name = "rag-agent"

      client_alias {
        dns_name = "rag-agent"
        port     = 8204
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_task_definition" "main_backend" {

  family                   = "banking-main-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "512"
  memory = "1024"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "main-backend"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-main:latest"
      essential = true

      portMappings = [
        {
          name          = "main-backend"
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      environment = local.common_environment

      secrets = local.common_secrets

      dependsOn = [
        {
          containerName = "otel-collector"
          condition     = "START"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "main-backend"
        }
      }
    },

    {
      name      = "otel-collector"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-otel-collector:latest"
      essential = false

      portMappings = [
        {
          name          = "otel-grpc"
          containerPort = 4317
          hostPort      = 4317
          protocol      = "tcp"
        },
        {
          name          = "otel-http"
          containerPort = 4318
          hostPort      = 4318
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "otel-collector"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


resource "aws_ecs_service" "main_backend" {

  name            = "main-backend"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.main_backend.arn

  desired_count          = 1
  launch_type            = "FARGATE"
  enable_execute_command = true
  network_configuration {
    subnets = local.private_subnets

    security_groups = [
      aws_security_group.main.id
    ]

    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main_backend.arn
    container_name   = "main-backend"
    container_port   = 8000
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn

    service {
      port_name      = "main-backend"
      discovery_name = "main-backend"

      client_alias {
        dns_name = "main-backend"
        port     = 8000
      }
    }
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

# ============================================================
# AGENT WORKER
# ============================================================

resource "aws_ecs_task_definition" "agent_worker" {

  family = "banking-agent-worker"

  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]

  cpu    = "512"
  memory = "1024"

  execution_role_arn = aws_iam_role.ecs_execution.arn
  task_role_arn      = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "agent-worker"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-agent-worker:latest"
      essential = true

      command = [
        "python",
        "-u",
        "-m",
        "app.worker.worker"
      ]

      environment = local.common_environment


      secrets = local.common_secrets

      dependsOn = [
        {
          containerName = "otel-collector"
          condition     = "START"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "agent-worker"
        }
      }
    },

    {
      name      = "otel-collector"
      image     = "131404648821.dkr.ecr.us-east-1.amazonaws.com/banking-otel-collector:latest"
      essential = false

      portMappings = [
        {
          name          = "otel-grpc"
          containerPort = 4317
          hostPort      = 4317
          protocol      = "tcp"
        },
        {
          name          = "otel-http"
          containerPort = 4318
          hostPort      = 4318
          protocol      = "tcp"
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"

        options = {
          awslogs-group         = "/ecs/banking-support"
          awslogs-region        = "us-east-1"
          awslogs-stream-prefix = "otel-collector"
        }
      }
    }
  ])

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

resource "aws_ecs_service" "agent_worker" {
  name            = "agent-worker"
  cluster         = aws_ecs_cluster.banking.id
  task_definition = aws_ecs_task_definition.agent_worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = local.private_subnets
    security_groups  = local.service_security_groups
    assign_public_ip = false
  }

  service_connect_configuration {
    enabled   = true
    namespace = aws_service_discovery_private_dns_namespace.banking.arn
  }

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

resource "aws_iam_policy" "agent_queue" {
  name = "banking-agent-queue-policy"

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "sqs:SendMessage"
        ]

        Resource = aws_sqs_queue.agent_jobs.arn
      },
      {
        Effect = "Allow"

        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]

        Resource = aws_sqs_queue.agent_jobs.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "agent_queue" {
  role       = aws_iam_role.ecs_task.name
  policy_arn = aws_iam_policy.agent_queue.arn
}

# ============================================================
# AGENT WORKER AUTOSCALING TARGET
# ============================================================

resource "aws_appautoscaling_target" "agent_worker" {

  min_capacity = 1
  max_capacity = 10

  resource_id = "service/${aws_ecs_cluster.banking.name}/${aws_ecs_service.agent_worker.name}"

  scalable_dimension = "ecs:service:DesiredCount"

  service_namespace = "ecs"

  depends_on = [
    aws_ecs_service.agent_worker
  ]
}

# ============================================================
# SQS BACKLOG SCALE OUT
# ============================================================

resource "aws_cloudwatch_metric_alarm" "agent_queue_scale_out" {

  alarm_name = "banking-agent-queue-scale-out"

  alarm_description = "Scale agent workers when SQS backlog increases"

  namespace = "AWS/SQS"

  metric_name = "ApproximateNumberOfMessagesVisible"

  statistic = "Average"

  period = 60

  evaluation_periods = 2

  threshold = 5

  comparison_operator = "GreaterThanOrEqualToThreshold"

  treat_missing_data = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.agent_jobs.name
  }

  alarm_actions = [
    aws_appautoscaling_policy.agent_worker_scale_out.arn
  ]

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

# ============================================================
# AGENT WORKER SCALE OUT POLICY
# ============================================================

resource "aws_appautoscaling_policy" "agent_worker_scale_out" {

  name = "banking-agent-worker-scale-out"

  policy_type = "StepScaling"

  resource_id = aws_appautoscaling_target.agent_worker.resource_id

  scalable_dimension = aws_appautoscaling_target.agent_worker.scalable_dimension

  service_namespace = aws_appautoscaling_target.agent_worker.service_namespace

  step_scaling_policy_configuration {

    adjustment_type = "ChangeInCapacity"

    cooldown = 60

    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_lower_bound = 0
      scaling_adjustment          = 1
    }
  }
}

# ============================================================
# SQS BACKLOG SCALE IN
# ============================================================

resource "aws_cloudwatch_metric_alarm" "agent_queue_scale_in" {

  alarm_name = "banking-agent-queue-scale-in"

  alarm_description = "Scale agent workers down when SQS queue remains empty"

  namespace = "AWS/SQS"

  metric_name = "ApproximateNumberOfMessagesVisible"

  statistic = "Average"

  period = 60

  evaluation_periods = 5

  threshold = 0

  comparison_operator = "LessThanOrEqualToThreshold"

  treat_missing_data = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.agent_jobs.name
  }

  alarm_actions = [
    aws_appautoscaling_policy.agent_worker_scale_in.arn
  ]

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

# ============================================================
# AGENT WORKER SCALE IN POLICY
# ============================================================

resource "aws_appautoscaling_policy" "agent_worker_scale_in" {

  name = "banking-agent-worker-scale-in"

  policy_type = "StepScaling"

  resource_id = aws_appautoscaling_target.agent_worker.resource_id

  scalable_dimension = aws_appautoscaling_target.agent_worker.scalable_dimension

  service_namespace = aws_appautoscaling_target.agent_worker.service_namespace

  step_scaling_policy_configuration {

    adjustment_type = "ChangeInCapacity"

    cooldown = 180

    metric_aggregation_type = "Average"

    step_adjustment {
      metric_interval_upper_bound = 0
      scaling_adjustment          = -1
    }
  }
}