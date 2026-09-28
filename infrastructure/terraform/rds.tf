resource "aws_db_subnet_group" "banking" {
  name = "banking-support-db-subnet-group"

  subnet_ids = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id
  ]

  tags = {
    Name      = "banking-support-db-subnet-group"
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

resource "aws_db_instance" "banking" {
  identifier = "banking-support-postgres"

  engine         = "postgres"
  engine_version = "16"

  instance_class        = "db.t4g.micro"
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "banking_support"
  username = var.db_username
  password = var.db_password
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.banking.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  publicly_accessible = false

  backup_retention_period = 0
  deletion_protection     = false
  skip_final_snapshot     = true

  multi_az = false

  tags = {
    Name      = "banking-support-postgres"
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}