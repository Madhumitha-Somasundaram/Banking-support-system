# ============================================================
# SCALABLE SERVICES
# ============================================================

locals {

  scalable_services = {
    main-backend = {
      service_name = "main-backend"
      max_capacity = 5
    }
    # DATA SERVICES

    account_service = {
      service_name = "account-service"
      max_capacity = 5
    }

    transaction_service = {
      service_name = "transaction-service"
      max_capacity = 5
    }

    card_service = {
      service_name = "card-service"
      max_capacity = 5
    }

    rag_service = {
      service_name = "rag-service"
      max_capacity = 5
    }


    # MCP SERVICES

    account_mcp = {
      service_name = "account-mcp"
      max_capacity = 5
    }

    transaction_mcp = {
      service_name = "transaction-mcp"
      max_capacity = 5
    }

    card_mcp = {
      service_name = "card-mcp"
      max_capacity = 5
    }

    rag_mcp = {
      service_name = "rag-mcp"
      max_capacity = 5
    }


    # DOMAIN AGENTS

    account_agent = {
      service_name = "account-agent"
      max_capacity = 5
    }

    transaction_agent = {
      service_name = "transaction-agent"
      max_capacity = 5
    }

    card_agent = {
      service_name = "card-agent"
      max_capacity = 5
    }

    rag_agent = {
      service_name = "rag-agent"
      max_capacity = 5
    }
  }
}


# ============================================================
# ECS SCALABLE TARGET
# ============================================================

resource "aws_appautoscaling_target" "ecs" {

  for_each = local.scalable_services

  min_capacity = 1
  max_capacity = each.value.max_capacity

  resource_id = "service/${aws_ecs_cluster.banking.name}/${each.value.service_name}"

  scalable_dimension = "ecs:service:DesiredCount"

  service_namespace = "ecs"

  depends_on = [
    aws_ecs_service.main_backend,
    aws_ecs_service.account_service,
    aws_ecs_service.transaction_service,
    aws_ecs_service.card_service,
    aws_ecs_service.rag_service,

    aws_ecs_service.account_mcp,
    aws_ecs_service.transaction_mcp,
    aws_ecs_service.card_mcp,
    aws_ecs_service.rag_mcp,

    aws_ecs_service.account_agent,
    aws_ecs_service.transaction_agent,
    aws_ecs_service.card_agent,
    aws_ecs_service.rag_agent
  ]
}


# ============================================================
# CPU AUTOSCALING
#
# Target:
#   60% average CPU
#
# Example:
#
# 1 task @ 85% CPU
#       ↓
# ECS adds another task
#
# 2 tasks @ low CPU
#       ↓
# ECS can scale back to 1
# ============================================================

resource "aws_appautoscaling_policy" "ecs_cpu" {

  for_each = local.scalable_services

  name = "banking-${each.key}-cpu"

  policy_type = "TargetTrackingScaling"

  resource_id = aws_appautoscaling_target.ecs[each.key].resource_id

  scalable_dimension = aws_appautoscaling_target.ecs[each.key].scalable_dimension

  service_namespace = aws_appautoscaling_target.ecs[each.key].service_namespace

  target_tracking_scaling_policy_configuration {

    target_value = 60

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }

    scale_out_cooldown = 60
    scale_in_cooldown  = 180

    disable_scale_in = false
  }
}


# ============================================================
# MEMORY AUTOSCALING
#
# Target:
#   70% average memory
#
# CPU OR MEMORY can cause scale-out.
# ============================================================

resource "aws_appautoscaling_policy" "ecs_memory" {

  for_each = local.scalable_services

  name = "banking-${each.key}-memory"

  policy_type = "TargetTrackingScaling"

  resource_id = aws_appautoscaling_target.ecs[each.key].resource_id

  scalable_dimension = aws_appautoscaling_target.ecs[each.key].scalable_dimension

  service_namespace = aws_appautoscaling_target.ecs[each.key].service_namespace

  target_tracking_scaling_policy_configuration {

    target_value = 70

    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }

    scale_out_cooldown = 60
    scale_in_cooldown  = 180

    disable_scale_in = false
  }
}