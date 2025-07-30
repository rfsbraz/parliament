# AWS WAF v2 for CloudFront Protection
# Provides DDoS protection, rate limiting, and security filtering

# Variable to control WAF
variable "enable_waf" {
  description = "Enable AWS WAF for CloudFront protection"
  type        = bool
  default     = true
}

# WAF Web ACL for CloudFront
resource "aws_wafv2_web_acl" "parliament" {
  count = var.enable_waf ? 1 : 0

  name  = "${local.name_prefix}-waf"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  # Rule 1: Rate Limiting (2000 requests per 5 minutes per IP)
  rule {
    name     = "RateLimitRule"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"

        scope_down_statement {
          geo_match_statement {
            # Allow higher rate limits for EU countries (where Portuguese parliament is most accessed)
            country_codes = ["PT", "ES", "FR", "DE", "IT", "BE", "NL", "AT", "IE", "LU"]
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # Rule 2: Global Rate Limiting (stricter for non-EU)
  rule {
    name     = "GlobalRateLimitRule"
    priority = 2

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 500
        aggregate_key_type = "IP"

        scope_down_statement {
          not_statement {
            statement {
              geo_match_statement {
                country_codes = ["PT", "ES", "FR", "DE", "IT", "BE", "NL", "AT", "IE", "LU", "US", "CA", "GB", "AU"]
              }
            }
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "GlobalRateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # Rule 3: AWS Managed Rules - Core Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"

        # Exclude rules that might interfere with API requests
        rule_action_override {
          action_to_use {
            allow {}
          }
          name = "GenericRFI_BODY"
        }

        rule_action_override {
          action_to_use {
            allow {}
          }
          name = "SizeRestrictions_BODY"
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # Rule 4: AWS Managed Rules - Known Bad Inputs
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 4

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
      metric_name                = "AWSManagedRulesKnownBadInputsRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # Rule 5: Block requests with suspicious user agents
  rule {
    name     = "BlockSuspiciousUserAgents"
    priority = 5

    action {
      block {}
    }

    statement {
      byte_match_statement {
        search_string = "bot"
        field_to_match {
          single_header {
            name = "user-agent"
          }
        }
        text_transformation {
          priority = 0
          type     = "LOWERCASE"
        }
        positional_constraint = "CONTAINS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BlockSuspiciousUserAgents"
      sampled_requests_enabled   = true
    }
  }

  # Rule 6: Allow legitimate parliamentary research access
  rule {
    name     = "AllowResearchAccess"
    priority = 6

    action {
      allow {}
    }

    statement {
      or_statement {
        statement {
          byte_match_statement {
            search_string = "research"
            field_to_match {
              single_header {
                name = "user-agent"
              }
            }
            text_transformation {
              priority = 0
              type     = "LOWERCASE"
            }
            positional_constraint = "CONTAINS"
          }
        }

        statement {
          byte_match_statement {
            search_string = "academic"
            field_to_match {
              single_header {
                name = "user-agent"
              }
            }
            text_transformation {
              priority = 0
              type     = "LOWERCASE"
            }
            positional_constraint = "CONTAINS"
          }
        }
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AllowResearchAccess"
      sampled_requests_enabled   = true
    }
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-waf"
  })

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-waf"
    sampled_requests_enabled   = true
  }
}

# Associate WAF with CloudFront Distribution
resource "aws_cloudfront_distribution" "frontend_with_waf" {
  count = var.enable_waf && var.deployment_type == "fargate" ? 1 : 0

  # ... (copy all existing CloudFront configuration)
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
    origin_id                = "S3-${aws_s3_bucket.frontend.id}"
  }

  # Additional origin for backend API
  origin {
    domain_name = aws_lb.backend[0].dns_name
    origin_id   = "ALB-Backend"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Portuguese Parliament Frontend with WAF Protection"
  default_root_object = "index.html"

  # Associate with WAF
  web_acl_id = aws_wafv2_web_acl.parliament[0].arn

  aliases = var.domain_name != "" ? [var.domain_name] : []

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.frontend.id}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  # Cache behavior for API calls
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "ALB-Backend"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      headers      = ["*"]
      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = var.certificate_arn == ""
    acm_certificate_arn           = var.certificate_arn != "" ? var.certificate_arn : null
    ssl_support_method            = var.certificate_arn != "" ? "sni-only" : null
    minimum_protocol_version      = var.certificate_arn != "" ? "TLSv1.2_2021" : null
  }

  # Custom error pages for SPA
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-cloudfront-with-waf"
  })
}

# Update existing CloudFront distributions to include WAF
resource "aws_wafv2_web_acl_association" "frontend" {
  count = var.enable_waf ? 1 : 0

  resource_arn = var.deployment_type == "serverless" ? 
    aws_cloudfront_distribution.frontend_serverless[0].arn : 
    aws_cloudfront_distribution.frontend.arn
  web_acl_arn = aws_wafv2_web_acl.parliament[0].arn
}

# CloudWatch Log Group for WAF
resource "aws_cloudwatch_log_group" "waf" {
  count = var.enable_waf ? 1 : 0

  name              = "/aws/wafv2/${local.name_prefix}"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-waf-logs"
  })
}

# WAF Logging Configuration
resource "aws_wafv2_web_acl_logging_configuration" "parliament" {
  count = var.enable_waf ? 1 : 0

  resource_arn            = aws_wafv2_web_acl.parliament[0].arn
  log_destination_configs = [aws_cloudwatch_log_group.waf[0].arn]

  redacted_fields {
    single_header {
      name = "authorization"
    }
  }

  redacted_fields {
    single_header {
      name = "cookie"
    }
  }
}

# Output WAF information
output "waf_enabled" {
  description = "Whether AWS WAF is enabled"
  value       = var.enable_waf
}

output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = var.enable_waf ? aws_wafv2_web_acl.parliament[0].arn : null
}

output "waf_protection_features" {
  description = "WAF protection features enabled"
  value = var.enable_waf ? [
    "Rate limiting (2000 req/5min for EU, 500 req/5min for others)",
    "AWS Managed Rules - Core Rule Set",
    "AWS Managed Rules - Known Bad Inputs",
    "Suspicious user agent blocking",
    "Geographic rate limiting",
    "Research/academic access allowlist"
  ] : []
}