# ============================================================
# AGENT JOB DEAD LETTER QUEUE
# ============================================================

resource "aws_sqs_queue" "agent_jobs_dlq" {

  name = "banking-agent-jobs-dlq"

  message_retention_seconds = 1209600

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}

resource "aws_iam_user_policy" "payanam_sqs" {
  user = "Payanam"
  name = "PayanamTerraformSQS"

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "sqs:CreateQueue"
        ]

        Resource = "*"
      },
      {
        Effect = "Allow"

        Action = [
          "sqs:DeleteQueue",
          "sqs:GetQueueUrl",
          "sqs:GetQueueAttributes",
          "sqs:SetQueueAttributes",
          "sqs:TagQueue",
          "sqs:UntagQueue",
          "sqs:ListQueueTags"
        ]

        Resource = "arn:aws:sqs:us-east-1:131404648821:*"
      },
      {
        Effect = "Allow"

        Action = [
          "sqs:ListQueues"
        ]

        Resource = "*"
      }
    ]
  })
}
# ============================================================
# AGENT JOB QUEUE
# ============================================================

resource "aws_sqs_queue" "agent_jobs" {

  name = "banking-agent-jobs"

  # Worker has up to 15 minutes to process a job.
  visibility_timeout_seconds = 900

  message_retention_seconds = 345600

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.agent_jobs_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Project   = "banking-support"
    ManagedBy = "terraform"
  }
}