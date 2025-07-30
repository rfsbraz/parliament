# Comprehensive Monitoring and Alerting for Portuguese Parliament System
# Provides operational visibility across Lambda, Aurora, CloudFront, and WAF

# Variable to control monitoring level
variable "enable_comprehensive_monitoring" {
  description = "Enable comprehensive monitoring dashboard and alerts"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email address for alerts (optional)"
  type        = string
  default     = ""
}

# SNS Topic for Alerts
resource "aws_sns_topic" "parliament_alerts" {
  count = var.enable_comprehensive_monitoring ? 1 : 0

  name = "${local.name_prefix}-alerts"

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-alerts"
  })
}

# SNS Topic Subscription (if email provided)
resource "aws_sns_topic_subscription" "email_alerts" {
  count = var.enable_comprehensive_monitoring && var.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.parliament_alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "parliament" {
  count = var.enable_comprehensive_monitoring ? 1 : 0

  dashboard_name = "${local.name_prefix}-operations"

  dashboard_body = jsonencode({
    widgets = [
      # Lambda Metrics (if serverless)
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = var.deployment_type == "serverless" ? [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.backend[0].function_name],
            [".", "Invocations", ".", "."],
            [".", "Errors", ".", "."],
            [".", "ConcurrentExecutions", ".", "."],
            [".", "Throttles", ".", "."]
          ] : []
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Performance Metrics"
          period  = 300
        }
      },

      # Aurora Metrics (if serverless)
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = var.deployment_type == "serverless" ? [
            ["AWS/RDS", "ServerlessDatabaseCapacity", "DBClusterIdentifier", aws_rds_cluster.parliament[0].cluster_identifier],
            [".", "DatabaseConnections", ".", "."],
            [".", "CPUUtilization", ".", "."],
            [".", "FreeableMemory", ".", "."]
          ] : []
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Aurora Serverless Metrics"
          period  = 300
        }
      },

      # ECS Metrics (if fargate)
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = var.deployment_type == "fargate" ? [
            ["AWS/ECS", "CPUUtilization", "ServiceName", aws_ecs_service.backend[0].name, "ClusterName", aws_ecs_cluster.backend[0].name],
            [".", "MemoryUtilization", ".", ".", ".", "."],
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.backend[0].arn_suffix],
            [".", "ResponseTime", ".", "."]
          ] : []
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "ECS Fargate Metrics"
          period  = 300
        }
      },

      # CloudFront Metrics
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/CloudFront", "Requests", "DistributionId", var.deployment_type == "serverless" ? aws_cloudfront_distribution.frontend_serverless[0].id : aws_cloudfront_distribution.frontend.id],
            [".", "BytesDownloaded", ".", "."],
            [".", "ErrorRate", ".", "."],
            [".", "CacheHitRate", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"  # CloudFront metrics are in us-east-1
          title   = "CloudFront Performance"
          period  = 300
        }
      },

      # WAF Metrics (if enabled)
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = var.enable_waf ? [
            ["AWS/WAFV2", "AllowedRequests", "WebACL", aws_wafv2_web_acl.parliament[0].name, "Rule", "ALL", "Region", "CloudFront"],
            [".", "BlockedRequests", ".", ".", ".", ".", ".", "."],
            [".", "SampledRequests", ".", ".", ".", ".", ".", "."]
          ] : []
          view    = "timeSeries"
          stacked = false
          region  = "us-east-1"  # WAF CloudFront metrics are in us-east-1
          title   = "WAF Security Metrics"
          period  = 300
        }
      },

      # Cost and Usage Metrics
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = var.deployment_type == "serverless" ? [
            ["AWS/Lambda", "Duration", "FunctionName", aws_lambda_function.backend[0].function_name],
            ["AWS/RDS", "ServerlessDatabaseCapacity", "DBClusterIdentifier", aws_rds_cluster.parliament[0].cluster_identifier]
          ] : [
            ["AWS/ECS", "CPUUtilization", "ServiceName", aws_ecs_service.backend[0].name, "ClusterName", aws_ecs_cluster.backend[0].name],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Resource Utilization"
          period  = 300
        }
      },

      # Log Insights Query Results
      {
        type   = "log"
        x      = 0
        y      = 18
        width  = 24
        height = 6

        properties = {
          query = var.deployment_type == "serverless" ? 
            "SOURCE '/aws/lambda/${local.name_prefix}-backend'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20" :
            "SOURCE '/ecs/${local.name_prefix}-backend'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20"
          region = var.aws_region
          title  = "Recent Errors"
        }
      }
    ]
  })
}

# Lambda-specific CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count = var.enable_comprehensive_monitoring && var.deployment_type == "serverless" ? 1 : 0

  alarm_name          = "${local.name_prefix}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Lambda function error rate is too high"
  alarm_actions       = [aws_sns_topic.parliament_alerts[0].arn]

  dimensions = {
    FunctionName = aws_lambda_function.backend[0].function_name
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-errors-alarm"
  })
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  count = var.enable_comprehensive_monitoring && var.deployment_type == "serverless" ? 1 : 0

  alarm_name          = "${local.name_prefix}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "10000"  # 10 seconds
  alarm_description   = "Lambda function duration is too high"
  alarm_actions       = [aws_sns_topic.parliament_alerts[0].arn]

  dimensions = {
    FunctionName = aws_lambda_function.backend[0].function_name
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-duration-alarm"
  })
}

# Aurora-specific CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "aurora_cpu" {
  count = var.enable_comprehensive_monitoring && var.deployment_type == "serverless" ? 1 : 0

  alarm_name          = "${local.name_prefix}-aurora-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "Aurora CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.parliament_alerts[0].arn]

  dimensions = {
    DBClusterIdentifier = aws_rds_cluster.parliament[0].cluster_identifier
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-aurora-cpu-alarm"
  })
}

resource "aws_cloudwatch_metric_alarm" "aurora_connections" {
  count = var.enable_comprehensive_monitoring && var.deployment_type == "serverless" ? 1 : 0

  alarm_name          = "${local.name_prefix}-aurora-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "40"  # 80% of default max_connections
  alarm_description   = "Aurora connection count is too high"
  alarm_actions       = [aws_sns_topic.parliament_alerts[0].arn]

  dimensions = {
    DBClusterIdentifier = aws_rds_cluster.parliament[0].cluster_identifier
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-aurora-connections-alarm"
  })
}

# ECS-specific CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "ecs_cpu" {
  count = var.enable_comprehensive_monitoring && var.deployment_type == "fargate" ? 1 : 0

  alarm_name          = "${local.name_prefix}-ecs-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "ECS CPU utilization is too high"
  alarm_actions       = [aws_sns_topic.parliament_alerts[0].arn]

  dimensions = {
    ServiceName = aws_ecs_service.backend[0].name
    ClusterName = aws_ecs_cluster.backend[0].name
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-ecs-cpu-alarm"
  })
}

# CloudFront Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "cloudfront_errors" {
  count = var.enable_comprehensive_monitoring ? 1 : 0

  alarm_name          = "${local.name_prefix}-cloudfront-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ErrorRate"
  namespace           = "AWS/CloudFront"
  period              = "300"
  statistic           = "Average"
  threshold           = "5"  # 5% error rate
  alarm_description   = "CloudFront error rate is too high"
  alarm_actions       = [aws_sns_topic.parliament_alerts[0].arn]

  dimensions = {
    DistributionId = var.deployment_type == "serverless" ? aws_cloudfront_distribution.frontend_serverless[0].id : aws_cloudfront_distribution.frontend.id
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-cloudfront-errors-alarm"
  })
}

# WAF Blocked Requests Alarm (high blocking might indicate attack)
resource "aws_cloudwatch_metric_alarm" "waf_blocked_requests" {
  count = var.enable_comprehensive_monitoring && var.enable_waf ? 1 : 0

  alarm_name          = "${local.name_prefix}-waf-high-blocks"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "BlockedRequests"
  namespace           = "AWS/WAFV2"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1000"  # More than 1000 blocked requests in 5 minutes
  alarm_description   = "WAF is blocking unusually high number of requests - possible attack"
  alarm_actions       = [aws_sns_topic.parliament_alerts[0].arn]

  dimensions = {
    WebACL = aws_wafv2_web_acl.parliament[0].name
    Rule   = "ALL"
    Region = "CloudFront"
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-waf-blocks-alarm"
  })
}

# Custom Metric: Application Health Check
resource "aws_cloudwatch_log_metric_filter" "application_health" {
  count = var.enable_comprehensive_monitoring ? 1 : 0

  name           = "${local.name_prefix}-app-health"
  log_group_name = var.deployment_type == "serverless" ? aws_cloudwatch_log_group.lambda_backend[0].name : aws_cloudwatch_log_group.backend[0].name
  pattern        = "[timestamp, requestId, level=\"ERROR\"]"

  metric_transformation {
    name      = "ApplicationErrors"
    namespace = "Parliament/Application"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "application_health" {
  count = var.enable_comprehensive_monitoring ? 1 : 0

  alarm_name          = "${local.name_prefix}-app-health"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ApplicationErrors"
  namespace           = "Parliament/Application"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "Application is generating too many errors"
  alarm_actions       = [aws_sns_topic.parliament_alerts[0].arn]
  treat_missing_data  = "notBreaching"

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-app-health-alarm"
  })
}

# Output monitoring information
output "monitoring_enabled" {
  description = "Whether comprehensive monitoring is enabled"
  value       = var.enable_comprehensive_monitoring
}

output "dashboard_url" {
  description = "CloudWatch Dashboard URL"
  value = var.enable_comprehensive_monitoring ? 
    "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${local.name_prefix}-operations" : 
    null
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = var.enable_comprehensive_monitoring ? aws_sns_topic.parliament_alerts[0].arn : null
}

output "monitoring_features" {
  description = "Monitoring features enabled"
  value = var.enable_comprehensive_monitoring ? [
    "CloudWatch Dashboard with key metrics",
    var.deployment_type == "serverless" ? "Lambda performance monitoring" : "ECS performance monitoring",
    var.deployment_type == "serverless" ? "Aurora Serverless capacity tracking" : "Application Load Balancer monitoring",
    "CloudFront performance and error tracking",
    var.enable_waf ? "WAF security metrics and attack detection" : null,
    "Application health monitoring via log analysis",
    "Automated alerting via SNS",
    var.alert_email != "" ? "Email notifications configured" : "Email notifications not configured"
  ] : []
}