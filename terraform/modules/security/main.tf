# Security Module
# Provides GuardDuty, Security Hub, enhanced WAF, and security monitoring

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "enable_guardduty" {
  description = "Enable GuardDuty"
  type        = bool
  default     = true
}

variable "enable_security_hub" {
  description = "Enable Security Hub"
  type        = bool
  default     = true
}

variable "enable_enhanced_waf" {
  description = "Enable enhanced WAF rules"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email for security alerts"
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

# GuardDuty
resource "aws_guardduty_detector" "main" {
  count = var.enable_guardduty ? 1 : 0

  enable                       = true
  finding_publishing_frequency = "FIFTEEN_MINUTES"

  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = false
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = false
        }
      }
    }
  }

  tags = var.tags
}

# Security Hub
resource "aws_securityhub_account" "main" {
  count = var.enable_security_hub ? 1 : 0

  enable_default_standards = true
  control_finding_generator = "SECURITY_CONTROL"
  auto_enable_controls      = true

  depends_on = [aws_guardduty_detector.main]
}

# Security Hub Standards
resource "aws_securityhub_standards_subscription" "aws_foundational" {
  count = var.enable_security_hub ? 1 : 0

  standards_arn = "arn:aws:securityhub:::ruleset/finding-format/aws-foundational-security-standard/v/1.0.0"
  depends_on    = [aws_securityhub_account.main]
}

resource "aws_securityhub_standards_subscription" "cis" {
  count = var.enable_security_hub ? 1 : 0

  standards_arn = "arn:aws:securityhub:::ruleset/finding-format/cis-aws-foundations-benchmark/v/1.2.0"
  depends_on    = [aws_securityhub_account.main]
}

# Enhanced WAF
resource "aws_wafv2_web_acl" "enhanced" {
  count = var.enable_enhanced_waf ? 1 : 0

  name  = "${local.name_prefix}-enhanced-waf"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # Core Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # Known Bad Inputs
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "KnownBadInputsRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # SQL Injection Protection
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLiRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # Rate Limiting
  rule {
    name     = "RateLimitRule"
    priority = 4

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitMetric"
      sampled_requests_enabled   = true
    }
  }

  # IP Reputation
  rule {
    name     = "AWSManagedRulesAmazonIpReputationList"
    priority = 5

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesAmazonIpReputationList"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "IpReputationMetric"
      sampled_requests_enabled   = true
    }
  }

  tags = var.tags

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}EnhancedWAF"
    sampled_requests_enabled   = true
  }
}

# WAF Logging
resource "aws_cloudwatch_log_group" "waf" {
  count = var.enable_enhanced_waf ? 1 : 0

  name              = "/aws/wafv2/${local.name_prefix}"
  retention_in_days = var.environment == "prod" ? 30 : 7
  tags              = var.tags
}

resource "aws_wafv2_web_acl_logging_configuration" "main" {
  count = var.enable_enhanced_waf ? 1 : 0

  resource_arn            = aws_wafv2_web_acl.enhanced[0].arn
  log_destination_configs = [aws_cloudwatch_log_group.waf[0].arn]

  redacted_field {
    single_header {
      name = "authorization"
    }
  }

  redacted_field {
    single_header {
      name = "cookie"
    }
  }
}

# Security Alerts SNS Topic
resource "aws_sns_topic" "security_alerts" {
  count = var.alert_email != "" ? 1 : 0
  name  = "${local.name_prefix}-security-alerts"
  tags  = var.tags
}

resource "aws_sns_topic_subscription" "security_email_alerts" {
  count = var.alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.security_alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# GuardDuty Findings Event Rule
resource "aws_cloudwatch_event_rule" "guardduty_findings" {
  count = var.enable_guardduty && var.alert_email != "" ? 1 : 0

  name        = "${local.name_prefix}-guardduty-findings"
  description = "Capture high severity GuardDuty findings"

  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Finding"]
    detail = {
      severity = [7.0, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 8.0, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 10.0]
    }
  })
}

resource "aws_cloudwatch_event_target" "guardduty_sns" {
  count = var.enable_guardduty && var.alert_email != "" ? 1 : 0

  rule      = aws_cloudwatch_event_rule.guardduty_findings[0].name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.security_alerts[0].arn
}

# SNS Topic Policy
resource "aws_sns_topic_policy" "security_alerts" {
  count = var.alert_email != "" ? 1 : 0
  arn   = aws_sns_topic.security_alerts[0].arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action   = "sns:Publish"
        Resource = aws_sns_topic.security_alerts[0].arn
      }
    ]
  })
}

# Outputs
output "guardduty_detector_id" {
  description = "GuardDuty detector ID"
  value       = var.enable_guardduty ? aws_guardduty_detector.main[0].id : null
}

output "security_hub_account_id" {
  description = "Security Hub account ID"
  value       = var.enable_security_hub ? aws_securityhub_account.main[0].id : null
}

output "waf_web_acl_arn" {
  description = "Enhanced WAF Web ACL ARN"
  value       = var.enable_enhanced_waf ? aws_wafv2_web_acl.enhanced[0].arn : null
}

output "waf_web_acl_id" {
  description = "Enhanced WAF Web ACL ID"
  value       = var.enable_enhanced_waf ? aws_wafv2_web_acl.enhanced[0].id : null
}

output "security_alerts_topic_arn" {
  description = "Security alerts SNS topic ARN"
  value       = var.alert_email != "" ? aws_sns_topic.security_alerts[0].arn : null
}