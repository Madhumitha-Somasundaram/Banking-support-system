resource "aws_secretsmanager_secret" "banking_app" {
  name        = "banking-support/app"
  description = "Secrets for Banking Support System"

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}