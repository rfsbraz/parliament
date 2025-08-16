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