output "vpc_id" {
  value = data.aws_vpc.existing.id
}

output "vpc_cidr" {
  value = data.aws_vpc.existing.cidr_block
}

output "ecr_repositories" {
  value = {
    for key, repo in aws_ecr_repository.services :
    key => repo.repository_url
  }
}

output "private_subnet_ids" {
  value = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id
  ]
}

output "private_subnet_cidrs" {
  value = [
    aws_subnet.private_a.cidr_block,
    aws_subnet.private_b.cidr_block
  ]
}

output "security_group_ids" {
  value = {
    alb      = aws_security_group.alb.id
    main     = aws_security_group.main.id
    services = aws_security_group.services.id
    rds      = aws_security_group.rds.id
  }
}

output "rds_endpoint" {
  value = aws_db_instance.banking.address
}

output "rds_port" {
  value = aws_db_instance.banking.port
}

output "banking_app_secret_arn" {
  description = "ARN of the Banking Support application secret"
  value       = aws_secretsmanager_secret.banking_app.arn
}

output "ecs_execution_role_arn" {
  description = "ECS task execution role ARN"
  value       = aws_iam_role.ecs_execution.arn
}

output "ecs_task_role_arn" {
  description = "ECS application task role ARN"
  value       = aws_iam_role.ecs_task.arn
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.banking.name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = aws_ecs_cluster.banking.arn
}