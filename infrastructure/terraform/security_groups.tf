resource "aws_security_group" "alb" {
  name        = "banking-alb-sg"
  description = "Security group for Banking Support ALB"
  vpc_id      = data.aws_vpc.existing.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "banking-alb-sg"
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

resource "aws_security_group" "main" {
  name        = "banking-main-sg"
  description = "Security group for Banking main backend"
  vpc_id      = data.aws_vpc.existing.id

  ingress {
    description     = "Main backend from ALB"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "banking-main-sg"
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

resource "aws_security_group" "services" {
  name        = "banking-services-sg"
  description = "Security group for internal Banking services"
  vpc_id      = data.aws_vpc.existing.id

  ingress {
    description     = "Traffic from main backend"
    from_port       = 8000
    to_port         = 8999
    protocol        = "tcp"
    security_groups = [aws_security_group.main.id]
  }

  ingress {
    description = "Internal ECS service traffic"
    from_port   = 8000
    to_port     = 8999
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.existing.cidr_block]
  }

  egress {
    description = "Outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "banking-services-sg"
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

resource "aws_security_group" "rds" {
  name        = "banking-rds-sg"
  description = "Security group for Banking PostgreSQL"
  vpc_id      = data.aws_vpc.existing.id

  ingress {
    description = "PostgreSQL from ECS services"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    security_groups = [
      aws_security_group.main.id,
      aws_security_group.services.id
    ]
  }

  egress {
    description = "Outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "banking-rds-sg"
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}