# Cost-Optimized Lambda Configuration
# Uses Function URL instead of API Gateway, 512MB memory, reserved concurrency
# Target cost: ~$5-8/month vs ~$15-20/month with API Gateway + provisioned concurrency

# Lambda function using AWS Lambda Web Adapter
resource "aws_lambda_function" "backend" {
  function_name = "${local.name_prefix}-backend"
  role          = aws_iam_role.lambda_execution.arn

  # Use container image
  package_type = "Image"
  image_uri    = var.backend_image

  # Optimized configuration for cost
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  # Reserved concurrency (free up to 1000)
  reserved_concurrent_executions = var.lambda_reserved_concurrency

  # Environment variables with in-memory caching
  environment {
    variables = {
      FLASK_ENV   = var.environment
      FLASK_DEBUG = var.environment == "dev" ? "1" : "0"

      # AWS Lambda Web Adapter configuration
      AWS_LWA_INVOKE_MODE = "response_stream"
      AWS_LWA_PORT        = "8000"

      # Database configuration - PostgreSQL
      DATABASE_TYPE       = "postgresql"
      DATABASE_SECRET_ARN = aws_secretsmanager_secret.db_credentials.arn
      DATABASE_NAME       = aws_db_instance.parliament.db_name

      # In-memory caching configuration
      ENABLE_CACHE      = var.enable_in_memory_cache ? "true" : "false"
      CACHE_TTL_SECONDS = tostring(var.cache_ttl_seconds)

      # Connection pooling configuration
      ENABLE_CONNECTION_POOLING = var.enable_connection_pooling ? "true" : "false"
      MAX_CONNECTIONS           = tostring(var.max_connections)

      # Disable external caching (Redis)
      ENABLE_REDIS_CACHE = "false"

      # Performance optimizations
      SQLALCHEMY_POOL_SIZE     = "3"
      SQLALCHEMY_POOL_RECYCLE  = "3600"
      SQLALCHEMY_POOL_PRE_PING = "true"

      # Logging level for cost optimization
      LOG_LEVEL = var.environment == "prod" ? "WARNING" : "INFO"
    }
  }

  # VPC configuration (required for RDS access)
  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-backend-lambda"
  })
}

# Lambda Function URL for direct HTTP access (replaces API Gateway)
resource "aws_lambda_function_url" "backend" {
  function_name      = aws_lambda_function.backend.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["*"]
    allow_headers     = ["date", "keep-alive", "content-type", "x-requested-with"]
    expose_headers    = ["date", "keep-alive"]
    max_age           = 86400
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-backend-lambda-url"
  })
}

# IAM Role for Lambda Execution
resource "aws_iam_role" "lambda_execution" {
  name = "${local.name_prefix}-lambda-execution"

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

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-execution-role"
  })
}

# Basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# VPC execution policy
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Lambda performance monitoring without X-Ray (cost optimization)
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count = var.enable_basic_monitoring ? 1 : 0

  alarm_name          = "${local.name_prefix}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Lambda function is experiencing errors"

  dimensions = {
    FunctionName = aws_lambda_function.backend.function_name
  }

  alarm_actions = var.alert_email != "" ? [aws_sns_topic.lambda_alerts[0].arn] : []

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-errors-alarm"
  })
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  count = var.enable_basic_monitoring ? 1 : 0

  alarm_name          = "${local.name_prefix}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = var.lambda_timeout * 1000 * 0.8 # 80% of timeout in milliseconds
  alarm_description   = "Lambda function duration is approaching timeout"

  dimensions = {
    FunctionName = aws_lambda_function.backend.function_name
  }

  alarm_actions = var.alert_email != "" ? [aws_sns_topic.lambda_alerts[0].arn] : []

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-duration-alarm"
  })
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  count = var.enable_basic_monitoring ? 1 : 0

  alarm_name          = "${local.name_prefix}-lambda-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Lambda function is being throttled"

  dimensions = {
    FunctionName = aws_lambda_function.backend.function_name
  }

  alarm_actions = var.alert_email != "" ? [aws_sns_topic.lambda_alerts[0].arn] : []

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-throttles-alarm"
  })
}

# CloudWatch Log Group for Lambda with cost-optimized retention
resource "aws_cloudwatch_log_group" "lambda_backend" {
  name              = "/aws/lambda/${local.name_prefix}-backend"
  retention_in_days = var.environment == "prod" ? 7 : 3 # Short retention for cost optimization

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-backend-logs"
  })
}

# Security Group for Lambda
resource "aws_security_group" "lambda" {
  name_prefix = "${local.name_prefix}-lambda-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for Lambda function"

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# SNS Topic for Lambda alerts
resource "aws_sns_topic" "lambda_alerts" {
  count = var.enable_basic_monitoring && var.alert_email != "" ? 1 : 0

  name = "${local.name_prefix}-lambda-alerts"

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-alerts"
  })
}

resource "aws_sns_topic_subscription" "lambda_alerts_email" {
  count = var.enable_basic_monitoring && var.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.lambda_alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Lambda warming function to prevent cold starts (optional, lightweight)
resource "aws_lambda_function" "warmer" {
  count = var.enable_basic_monitoring ? 1 : 0

  function_name = "${local.name_prefix}-warmer"
  role          = aws_iam_role.warmer_execution[0].arn

  filename         = "warmer.zip"
  source_code_hash = data.archive_file.warmer[0].output_base64sha256
  handler          = "index.handler"
  runtime          = "python3.9"
  timeout          = 10
  memory_size      = 128 # Minimal memory

  environment {
    variables = {
      FUNCTION_URL = aws_lambda_function_url.backend.function_url
    }
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-warmer"
  })
}

# Archive for warmer function
data "archive_file" "warmer" {
  count = var.enable_basic_monitoring ? 1 : 0

  type        = "zip"
  output_path = "warmer.zip"
  source {
    content  = <<EOF
import json
import urllib3

def handler(event, context):
    http = urllib3.PoolManager()
    try:
        # Simple health check to warm up the function
        response = http.request('GET', '${aws_lambda_function_url.backend.function_url}/health')
        return {
            'statusCode': 200,
            'body': json.dumps('Warmed up successfully')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
EOF
    filename = "index.py"
  }
}

# IAM Role for warmer function
resource "aws_iam_role" "warmer_execution" {
  count = var.enable_basic_monitoring ? 1 : 0

  name = "${local.name_prefix}-warmer-execution"

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

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-warmer-execution-role"
  })
}

resource "aws_iam_role_policy_attachment" "warmer_basic" {
  count = var.enable_basic_monitoring ? 1 : 0

  role       = aws_iam_role.warmer_execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# EventBridge rule to warm up Lambda periodically
resource "aws_cloudwatch_event_rule" "lambda_warmer" {
  count = var.enable_basic_monitoring ? 1 : 0

  name                = "${local.name_prefix}-lambda-warmer"
  description         = "Warm up Lambda function every 5 minutes"
  schedule_expression = "rate(5 minutes)"

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-warmer-rule"
  })
}

resource "aws_cloudwatch_event_target" "lambda_warmer" {
  count = var.enable_basic_monitoring ? 1 : 0

  rule      = aws_cloudwatch_event_rule.lambda_warmer[0].name
  target_id = "LambdaWarmerTarget"
  arn       = aws_lambda_function.warmer[0].arn
}

resource "aws_lambda_permission" "allow_cloudwatch_warmer" {
  count = var.enable_basic_monitoring ? 1 : 0

  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.warmer[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_warmer[0].arn
}