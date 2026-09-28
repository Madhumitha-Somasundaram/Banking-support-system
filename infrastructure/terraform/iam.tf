# ---------------------------------------------------------
# ECS Task Execution Role
# ---------------------------------------------------------

resource "aws_iam_role" "ecs_execution" {
  name = "banking-support-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_policy" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}


# ---------------------------------------------------------
# ECS Task Role
# ---------------------------------------------------------

resource "aws_iam_role" "ecs_task" {
  name = "banking-support-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}


# ---------------------------------------------------------
# Allow ECS applications to read our application secret
# ---------------------------------------------------------

resource "aws_iam_role_policy" "ecs_execution_secret_access" {
  name = "banking-support-execution-secret-access"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = aws_secretsmanager_secret.banking_app.arn
    }]
  })
}

