variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "Existing VPC ID"
  type        = string
  default     = "vpc-0faff2160ee1b47e6"
}

variable "db_username" {
  description = "Master username for PostgreSQL"
  type        = string
  default     = "banking_admin"
}

variable "db_password" {
  description = "Master password for PostgreSQL"
  type        = string
  sensitive   = true
}

variable "opensearch_url" {
  description = "OpenSearch endpoint URL"
  type        = string
}

variable "knowledge_s3_bucket" {
  description = "S3 bucket containing the banking knowledge base"
  type        = string
}

variable "bedrock_embedding_model" {
  description = "Bedrock embedding model ID"
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "public_subnets" {
  type = list(string)
}

variable "private_subnets" {
  type = list(string)
}