# Lambda Warming Strategy to Reduce Cold Starts
# Uses EventBridge to periodically invoke Lambda functions

# Variable to control Lambda warming
variable "enable_lambda_warming" {
  description = "Enable Lambda warming to reduce cold starts"
  type        = bool
  default     = false  # Will be enabled automatically for prod
}

variable "warming_schedule" {
  description = "EventBridge schedule for Lambda warming (rate expression)"
  type        = string
  default     = "rate(10 minutes)"  # Warm every 10 minutes
}

# EventBridge Rule for Lambda Warming (Production Only)
resource "aws_cloudwatch_event_rule" "lambda_warming" {
  count = (var.enable_lambda_warming || var.environment == "prod") && var.deployment_type == "serverless" ? 1 : 0

  name                = "${local.name_prefix}-lambda-warming"
  description         = "Trigger Lambda warming to prevent cold starts"
  schedule_expression = var.warming_schedule

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-warming-rule"
  })
}

# EventBridge Target (Lambda Function)
resource "aws_cloudwatch_event_target" "lambda_warming" {
  count = (var.enable_lambda_warming || var.environment == "prod") && var.deployment_type == "serverless" ? 1 : 0

  rule      = aws_cloudwatch_event_rule.lambda_warming[0].name
  target_id = "LambdaWarmingTarget"
  arn       = aws_lambda_function.backend[0].arn

  # Send warming event
  input = jsonencode({
    source        = "aws.events"
    warmer        = true
    detail-type   = "Scheduled Event"
    detail = {
      warming = true
      timestamp = "$${time}"
    }
  })
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge_warming" {
  count = (var.enable_lambda_warming || var.environment == "prod") && var.deployment_type == "serverless" ? 1 : 0

  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backend[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_warming[0].arn
}

# Enhanced Lambda Function with Warming Support
resource "aws_lambda_function" "backend_with_warming" {
  count = var.deployment_type == "serverless" ? 1 : 0

  function_name = "${local.name_prefix}-backend"
  role         = aws_iam_role.lambda_execution[0].arn
  
  # Use container image
  package_type = "Image"
  image_uri    = var.backend_serverless_image
  
  # Memory and timeout configuration
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout
  
  # Environment variables
  environment {
    variables = {
      FLASK_ENV   = var.environment
      FLASK_DEBUG = var.environment == "dev" ? "1" : "0"
      # AWS Lambda Web Adapter configuration
      AWS_LWA_INVOKE_MODE = "response_stream"
      AWS_LWA_PORT       = "8000"
      # Database configuration
      DATABASE_TYPE = "mysql"
      DATABASE_HOST_SECRET_ARN = var.deployment_type == "serverless" ? aws_rds_cluster.parliament[0].master_user_secret[0].secret_arn : ""
      DATABASE_NAME = "parliament"
      # Warming configuration (auto-enabled for prod)
      ENABLE_WARMING = (var.enable_lambda_warming || var.environment == "prod") ? "true" : "false"
    }
  }

  # VPC configuration for Aurora access
  dynamic "vpc_config" {
    for_each = var.lambda_vpc_enabled ? [1] : []
    content {
      subnet_ids         = aws_subnet.private[*].id
      security_group_ids = [aws_security_group.lambda[0].id]
    }
  }

  # Reserved concurrency (optional, for production workloads)
  reserved_concurrent_executions = var.environment == "prod" ? 5 : -1

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-backend-lambda"
  })

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_cloudwatch_log_group.lambda_backend,
  ]
}

# Provisioned Concurrency (for production environments with consistent traffic)
resource "aws_lambda_provisioned_concurrency_config" "backend" {
  count = (var.enable_lambda_warming || var.environment == "prod") && var.deployment_type == "serverless" && var.environment == "prod" ? 1 : 0

  function_name                     = aws_lambda_function.backend[0].function_name
  provisioned_concurrent_executions = 1  # Keep 1 instance warm
  qualifier                        = aws_lambda_function.backend[0].version

  # Only enable during business hours (optional cost optimization)
  lifecycle {
    ignore_changes = [provisioned_concurrent_executions]
  }
}

# CloudWatch Alarm for Cold Starts
resource "aws_cloudwatch_metric_alarm" "lambda_cold_starts" {
  count = (var.enable_lambda_warming || var.environment == "prod") && var.deployment_type == "serverless" ? 1 : 0

  alarm_name          = "${local.name_prefix}-lambda-cold-starts"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  
  # Custom metric filter to detect cold starts
  metric_name = "ColdStarts"
  namespace   = "AWS/Lambda"
  period      = "300"
  statistic   = "Sum"
  threshold   = "5"  # More than 5 cold starts in 5 minutes
  
  alarm_description = "Lambda function is experiencing too many cold starts"
  alarm_actions     = var.enable_comprehensive_monitoring ? [aws_sns_topic.parliament_alerts[0].arn] : []

  dimensions = {
    FunctionName = aws_lambda_function.backend[0].function_name
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-cold-starts-alarm"
  })
}

# Log Metric Filter to Track Cold Starts
resource "aws_cloudwatch_log_metric_filter" "cold_starts" {
  count = (var.enable_lambda_warming || var.environment == "prod") && var.deployment_type == "serverless" ? 1 : 0

  name           = "${local.name_prefix}-cold-starts"
  log_group_name = aws_cloudwatch_log_group.lambda_backend[0].name
  pattern        = "[timestamp, requestId, level=\"INFO\", msg=\"INIT_START\"]"

  metric_transformation {
    name      = "ColdStarts"
    namespace = "Parliament/Lambda"
    value     = "1"
  }
}

# X-Ray Tracing for Performance Analysis
resource "aws_lambda_function" "backend_with_xray" {
  count = var.deployment_type == "serverless" ? 1 : 0

  # ... (same configuration as above)
  function_name = "${local.name_prefix}-backend"
  role         = aws_iam_role.lambda_execution[0].arn
  package_type = "Image"
  image_uri    = var.backend_serverless_image
  memory_size  = var.lambda_memory_size
  timeout      = var.lambda_timeout

  # Enable X-Ray tracing
  tracing_config {
    mode = var.environment == "prod" ? "Active" : "PassThrough"
  }

  environment {
    variables = {
      FLASK_ENV   = var.environment
      FLASK_DEBUG = var.environment == "dev" ? "1" : "0"
      AWS_LWA_INVOKE_MODE = "response_stream"
      AWS_LWA_PORT       = "8000"
      DATABASE_TYPE = "mysql"
      DATABASE_HOST_SECRET_ARN = var.deployment_type == "serverless" ? aws_rds_cluster.parliament[0].master_user_secret[0].secret_arn : ""
      DATABASE_NAME = "parliament"
      ENABLE_WARMING = (var.enable_lambda_warming || var.environment == "prod") ? "true" : "false"
      # X-Ray configuration
      _X_AMZN_TRACE_ID = ""
      AWS_XRAY_TRACING_NAME = "${local.name_prefix}-backend"
    }
  }

  dynamic "vpc_config" {
    for_each = var.lambda_vpc_enabled ? [1] : []
    content {
      subnet_ids         = aws_subnet.private[*].id
      security_group_ids = [aws_security_group.lambda[0].id]
    }
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-backend-lambda"
  })
}

# X-Ray IAM permissions
resource "aws_iam_role_policy" "lambda_xray" {
  count = var.deployment_type == "serverless" && var.environment == "prod" ? 1 : 0

  name = "${local.name_prefix}-lambda-xray"
  role = aws_iam_role.lambda_execution[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords"
        ]
        Resource = "*"
      }
    ]
  })
}

# Output warming information
output "lambda_warming_enabled" {
  description = "Whether Lambda warming is enabled"
  value       = (var.enable_lambda_warming || var.environment == "prod") && var.deployment_type == "serverless"
}

output "warming_schedule" {
  description = "Lambda warming schedule"
  value       = (var.enable_lambda_warming || var.environment == "prod") && var.deployment_type == "serverless" ? var.warming_schedule : null
}

output "provisioned_concurrency" {
  description = "Provisioned concurrency configuration"
  value = (var.enable_lambda_warming || var.environment == "prod") && var.deployment_type == "serverless" && var.environment == "prod" ? {
    enabled = true
    concurrent_executions = 1
    estimated_cost = "$13.50/month for 1 provisioned execution"
  } : {
    enabled = false
    reason = var.environment != "prod" ? "Disabled for non-production environments" : "Warming via EventBridge only"
  }
}

output "cold_start_mitigation" {
  description = "Cold start mitigation strategies implemented"
  value = (var.enable_lambda_warming || var.environment == "prod") && var.deployment_type == "serverless" ? [
    "EventBridge warming every ${var.warming_schedule}",
    var.environment == "prod" ? "Provisioned concurrency (1 execution)" : null,
    "CloudWatch monitoring for cold start detection",
    "X-Ray tracing for performance analysis",
    "Reserved concurrency to prevent throttling"
  ] : var.deployment_type == "serverless" ? [
    "Cold starts accepted for dev environment (cost optimization)",
    "First request after idle period may take 1-3 seconds"
  ] : []
}