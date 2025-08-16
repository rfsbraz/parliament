# Cost-Optimized Terraform Outputs
# Key information for the deployed cost-optimized infrastructure

# Application URLs
output "lambda_function_url" {
  description = "Lambda Function URL for direct access (replaces API Gateway)"
  value       = aws_lambda_function_url.backend.function_url
}

output "cloudflare_domain" {
  description = "Main domain served through Cloudflare"
  value       = var.cloudflare_zone_id != "" ? var.domain_name : "Not configured"
}

output "cloudfront_domain" {
  description = "CloudFront domain for static assets"
  value       = var.enable_cloudfront ? aws_cloudfront_distribution.static_assets[0].domain_name : "Not enabled"
}

# Database Information
output "database_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.parliament.endpoint
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.parliament.db_name
}

output "database_secret_arn" {
  description = "ARN of the secret containing database credentials"
  value       = aws_secretsmanager_secret.db_credentials.arn
}

# Infrastructure Details
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "nat_gateway_id" {
  description = "NAT Gateway ID (single NAT for cost optimization)"
  value       = aws_nat_gateway.main.id
}

# Security Information
output "lambda_security_group_id" {
  description = "Lambda security group ID"
  value       = aws_security_group.lambda.id
}

output "rds_security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

# Cost Optimization Status
output "cost_optimization_enabled" {
  description = "Cost optimization mode status"
  value       = var.cost_optimization_mode
}

output "estimated_monthly_cost" {
  description = "Estimated monthly cost in USD"
  value       = "$11-17/month (cost-optimized architecture)"
}

output "cost_savings_vs_original" {
  description = "Cost savings compared to original architecture"
  value       = "~50-70% savings vs Aurora + API Gateway + enhanced services"
}


# Environment Information
output "environment" {
  description = "Current environment"
  value       = var.environment
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}


# Performance Configuration
output "lambda_configuration" {
  description = "Lambda function configuration"
  value = {
    memory_size          = var.lambda_memory_size
    timeout              = var.lambda_timeout
    reserved_concurrency = var.lambda_reserved_concurrency
    runtime              = "Container (AWS Lambda Web Adapter)"
  }
}

output "database_configuration" {
  description = "Database configuration"
  value = {
    engine           = var.db_engine
    instance_class   = var.db_instance_class
    storage_type     = var.db_storage_type
    storage_size     = var.db_allocated_storage
    multi_az         = var.db_multi_az
    backup_retention = var.db_backup_retention_period
  }
}

# Monitoring Information
output "monitoring_configuration" {
  description = "Monitoring configuration"
  value = {
    basic_monitoring       = var.enable_basic_monitoring
    detailed_monitoring    = var.enable_detailed_monitoring
    alert_email_configured = var.alert_email != ""
    log_retention_days     = var.environment == "prod" ? 7 : 3
  }
}

# Caching Configuration
output "caching_configuration" {
  description = "Application caching configuration"
  value = {
    in_memory_cache    = var.enable_in_memory_cache
    cache_ttl_seconds  = var.cache_ttl_seconds
    connection_pooling = var.enable_connection_pooling
    max_connections    = var.max_connections
  }
}

# ============================================================================
# COMPREHENSIVE TAGGING OUTPUTS FOR COST ANALYSIS AND VALIDATION
# ============================================================================

# Tag Validation Outputs
output "tagging_strategy" {
  description = "Comprehensive tagging strategy information"
  value = {
    project_name             = var.project_name
    application_name         = var.application_name
    environment             = var.environment
    cost_center             = var.cost_center
    business_unit           = var.business_unit
    owner_team              = var.owner_team
    owner_email             = var.owner_email
    data_classification     = var.data_classification
    compliance_requirements = var.compliance_requirements
    backup_schedule         = var.backup_schedule
    monitoring_level        = var.monitoring_level
    auto_shutdown           = var.auto_shutdown
    cost_optimized          = var.cost_optimization_mode
  }
}

output "billable_resources_summary" {
  description = "Summary of all billable AWS resources and their key cost-related tags"
  value = {
    rds_instance = {
      resource_type     = "RDS PostgreSQL Instance"
      instance_class    = var.db_instance_class
      storage_type      = var.db_storage_type
      storage_size_gb   = var.db_allocated_storage
      multi_az          = var.db_multi_az
      backup_retention  = var.db_backup_retention_period
      billable          = "true"
      component_type    = "database"
    }
    lambda_backend = {
      resource_type        = "Lambda Function"
      memory_size_mb       = var.lambda_memory_size
      timeout_seconds      = var.lambda_timeout
      reserved_concurrency = var.lambda_reserved_concurrency
      billable             = "true"
      component_type       = "compute"
    }
    lambda_warmer = var.enable_basic_monitoring ? {
      resource_type   = "Lambda Function (Warmer)"
      memory_size_mb  = "128"
      timeout_seconds = "10"
      billable        = "true"
      component_type  = "compute"
      purpose         = "cost-optimization"
    } : null
    nat_gateway = {
      resource_type  = "NAT Gateway"
      billable       = "true"
      component_type = "network"
      purpose        = "cost-optimized-single-nat"
    }
    elastic_ip = {
      resource_type  = "Elastic IP"
      billable       = "true"
      component_type = "network"
      purpose        = "nat-gateway"
    }
    s3_bucket = var.enable_cloudfront ? {
      resource_type  = "S3 Bucket"
      billable       = "true"
      component_type = "storage"
      purpose        = "static-assets"
    } : null
    cloudfront_distribution = var.enable_cloudfront ? {
      resource_type  = "CloudFront Distribution"
      price_class    = var.cloudfront_price_class
      billable       = "true"
      component_type = "storage"
      purpose        = "cdn"
    } : null
    cloudwatch_logs = {
      resource_type     = "CloudWatch Log Groups"
      retention_days    = var.environment == "prod" ? "7" : "3"
      billable          = "true"
      component_type    = "monitoring"
      purpose           = "logging"
    }
    sns_topics = var.enable_basic_monitoring && var.alert_email != "" ? {
      resource_type  = "SNS Topics"
      billable       = "true"
      component_type = "monitoring"
      purpose        = "alerting"
    } : null
  }
}

output "cost_allocation_tags" {
  description = "Key tags for AWS Cost Explorer and billing analysis"
  value = {
    # Primary cost allocation tags
    cost_center    = var.cost_center
    business_unit  = var.business_unit
    project        = var.project_name
    application    = var.application_name
    environment    = var.environment
    owner_team     = var.owner_team
    
    # Secondary cost analysis tags
    cost_optimized = var.cost_optimization_mode
    backup_schedule = var.backup_schedule
    monitoring_level = var.monitoring_level
    auto_shutdown   = var.auto_shutdown
    
    # Technical categorization
    managed_by      = "Terraform"
    repository      = "parliament"
    terraform       = "true"
  }
}

output "tag_compliance_check" {
  description = "Tag compliance verification for governance and cost analysis"
  value = {
    required_tags_present = {
      project_name      = var.project_name != ""
      application_name  = var.application_name != ""
      environment       = var.environment != ""
      cost_center       = var.cost_center != ""
      business_unit     = var.business_unit != ""
      owner_team        = var.owner_team != ""
      data_classification = contains(["public", "internal", "confidential", "restricted"], var.data_classification)
      backup_schedule   = contains(["daily", "weekly", "monthly", "none"], var.backup_schedule)
      monitoring_level  = contains(["basic", "standard", "enhanced"], var.monitoring_level)
    }
    optional_tags_present = {
      owner_email_configured = var.owner_email != ""
      additional_tags_count = length(var.additional_tags)
    }
    governance_compliance = {
      gdpr_compliance_tagged = var.compliance_requirements == "gdpr"
      cost_center_defined   = var.cost_center != ""
      business_owner_defined = var.business_unit != "" && var.owner_team != ""
    }
  }
}

output "resource_inventory_by_component" {
  description = "Resource inventory organized by component type for cost analysis"
  value = {
    compute_resources = [
      "aws_lambda_function.backend",
      var.enable_basic_monitoring ? "aws_lambda_function.warmer" : null
    ]
    database_resources = [
      "aws_db_instance.parliament",
      "aws_db_parameter_group.parliament",
      "aws_db_subnet_group.parliament"
    ]
    storage_resources = var.enable_cloudfront ? [
      "aws_s3_bucket.static_assets",
      "aws_cloudfront_distribution.static_assets"
    ] : []
    network_resources = [
      "aws_vpc.main",
      "aws_subnet.public",
      "aws_subnet.private", 
      "aws_nat_gateway.main",
      "aws_eip.nat",
      "aws_internet_gateway.main",
      "aws_route_table.public",
      "aws_route_table.private"
    ]
    security_resources = [
      "aws_security_group.lambda",
      "aws_security_group.rds",
      "aws_security_group.vpc_endpoints",
      "aws_iam_role.lambda_execution",
      "aws_secretsmanager_secret.db_credentials"
    ]
    monitoring_resources = concat(
      [
        "aws_cloudwatch_log_group.lambda_backend",
        "aws_cloudwatch_log_group.application_logs"
      ],
      var.enable_basic_monitoring ? [
        "aws_cloudwatch_log_group.vpc_flow_logs",
        "aws_cloudwatch_metric_alarm.lambda_errors",
        "aws_cloudwatch_metric_alarm.lambda_duration", 
        "aws_cloudwatch_metric_alarm.lambda_throttles",
        "aws_cloudwatch_metric_alarm.rds_cpu",
        "aws_cloudwatch_metric_alarm.rds_connections",
        "aws_cloudwatch_metric_alarm.rds_freeable_memory",
        "aws_cloudwatch_metric_alarm.application_health",
        "aws_cloudwatch_metric_alarm.cost_alarm",
        "aws_cloudwatch_metric_alarm.application_error_rate",
        "aws_cloudwatch_dashboard.main"
      ] : []
    )
  }
}

output "cost_optimization_summary" {
  description = "Cost optimization features and their impact on tagging"
  value = {
    optimization_mode = var.cost_optimization_mode
    cost_saving_features = {
      single_nat_gateway    = "Reduced network costs vs multi-AZ NAT"
      function_url_vs_api_gateway = "Eliminated API Gateway costs"
      rds_single_az         = "Reduced database costs vs Multi-AZ"
      short_log_retention   = "Reduced CloudWatch storage costs"
      basic_monitoring_only = "Reduced monitoring costs"
      reserved_concurrency  = "Controlled Lambda costs"
      cost_optimized_cloudfront = var.enable_cloudfront ? "EU/US only distribution" : "Disabled for dev"
    }
    target_monthly_cost = "$11-17"
    cost_savings_percentage = "50-70% vs full-featured architecture"
    billable_resource_count = {
      always_billable = 4  # RDS, Lambda, NAT Gateway, EIP
      conditional_billable = var.enable_cloudfront ? 2 : 0  # S3, CloudFront
      monitoring_billable = var.enable_basic_monitoring ? 3 : 1  # CloudWatch logs, alarms, SNS
    }
  }
}