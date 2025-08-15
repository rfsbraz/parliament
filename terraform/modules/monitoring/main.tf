# Comprehensive Monitoring Module
# Provides CloudWatch dashboards, Synthetics, X-Ray tracing, and alerting

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "enable_synthetics" {
  description = "Enable CloudWatch Synthetics"
  type        = bool
  default     = true
}

variable "enable_xray_tracing" {
  description = "Enable X-Ray tracing"
  type        = bool
  default     = true
}

variable "synthetics_frequency" {
  description = "Synthetics frequency in minutes"
  type        = number
  default     = 5
}

variable "alert_email" {
  description = "Email for alerts"
  type        = string
  default     = ""
}

variable "domain_name" {
  description = "Domain name for monitoring"
  type        = string
}

variable "lambda_function_name" {
  description = "Lambda function name to monitor"
  type        = string
}

variable "aurora_cluster_id" {
  description = "Aurora cluster identifier"
  type        = string
}

variable "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  type        = string
}

variable "redis_cluster_id" {
  description = "Redis cluster ID"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  count = var.alert_email != "" ? 1 : 0
  name  = "${local.name_prefix}-monitoring-alerts"
  tags  = var.tags
}

resource "aws_sns_topic_subscription" "email_alerts" {
  count = var.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# S3 Bucket for Synthetics artifacts
resource "aws_s3_bucket" "synthetics_artifacts" {
  count = var.enable_synthetics ? 1 : 0

  bucket        = "${local.name_prefix}-synthetics-${random_string.bucket_suffix[0].result}"
  force_destroy = true
  tags          = var.tags
}

resource "random_string" "bucket_suffix" {
  count = var.enable_synthetics ? 1 : 0

  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket_public_access_block" "synthetics_artifacts" {
  count = var.enable_synthetics ? 1 : 0

  bucket                  = aws_s3_bucket.synthetics_artifacts[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM Role for Synthetics
resource "aws_iam_role" "synthetics_execution" {
  count = var.enable_synthetics ? 1 : 0

  name = "${local.name_prefix}-synthetics-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "synthetics_execution" {
  count = var.enable_synthetics ? 1 : 0

  name = "${local.name_prefix}-synthetics-execution"
  role = aws_iam_role.synthetics_execution[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:GetBucketLocation",
          "cloudwatch:PutMetricData",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

# Synthetics Canaries
resource "aws_synthetics_canary" "homepage" {
  count = var.enable_synthetics ? 1 : 0

  name                 = "${local.name_prefix}-homepage-monitor"
  artifact_s3_location = "s3://${aws_s3_bucket.synthetics_artifacts[0].bucket}/homepage/"
  execution_role_arn   = aws_iam_role.synthetics_execution[0].arn
  handler              = "pageLoadBlueprint.handler"
  zip_file             = "pageLoadBlueprint.js"
  runtime_version      = "syn-nodejs-puppeteer-6.2"

  schedule {
    expression          = "rate(${var.synthetics_frequency} minutes)"
    duration_in_seconds = 0
  }

  run_config {
    timeout_in_seconds    = 60
    memory_in_mb         = 960
    active_tracing       = var.enable_xray_tracing
    environment_variables = {
      URL = "https://${var.domain_name}"
    }
  }

  success_retention_period = 2
  failure_retention_period = 14
  tags                     = var.tags
}

resource "aws_synthetics_canary" "api_health" {
  count = var.enable_synthetics ? 1 : 0

  name                 = "${local.name_prefix}-api-health-monitor"
  artifact_s3_location = "s3://${aws_s3_bucket.synthetics_artifacts[0].bucket}/api/"
  execution_role_arn   = aws_iam_role.synthetics_execution[0].arn
  handler              = "apiCanaryBlueprint.handler"
  zip_file             = "apiCanaryBlueprint.js"
  runtime_version      = "syn-nodejs-puppeteer-6.2"

  schedule {
    expression          = "rate(${var.synthetics_frequency} minutes)"
    duration_in_seconds = 0
  }

  run_config {
    timeout_in_seconds    = 30
    memory_in_mb         = 960
    active_tracing       = var.enable_xray_tracing
    environment_variables = {
      API_URL = "https://${var.domain_name}/api/health"
    }
  }

  success_retention_period = 2
  failure_retention_period = 14
  tags                     = var.tags
}

# Enhanced CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${local.name_prefix}-monitoring"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = var.enable_synthetics ? [
            ["CloudWatchSynthetics", "SuccessPercent", "CanaryName", aws_synthetics_canary.homepage[0].name],
            [".", "Duration", ".", "."],
            [".", "SuccessPercent", "CanaryName", aws_synthetics_canary.api_health[0].name],
            [".", "Duration", ".", "."]
          ] : []
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Synthetics Monitoring"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", var.lambda_function_name],
            [".", "Invocations", ".", "."],
            [".", "Errors", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Performance"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBClusterIdentifier", var.aurora_cluster_id],
            [".", "CPUUtilization", ".", "."],
            [".", "ServerlessDatabaseCapacity", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Database Performance"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/CloudFront", "Requests", "DistributionId", var.cloudfront_distribution_id],
            [".", "ErrorRate", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"
          title   = "CloudFront Performance"
          period  = 300
        }
      }
    ]
  })
}

# Output values
output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = var.alert_email != "" ? aws_sns_topic.alerts[0].arn : null
}

output "dashboard_url" {
  description = "CloudWatch Dashboard URL"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${local.name_prefix}-monitoring"
}

output "synthetics_canary_names" {
  description = "Names of created Synthetics canaries"
  value = var.enable_synthetics ? [
    aws_synthetics_canary.homepage[0].name,
    aws_synthetics_canary.api_health[0].name
  ] : []
}