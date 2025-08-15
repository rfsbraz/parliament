# Cost-Optimized Variables for Portuguese Parliament Transparency Application
# Target: $11-17/month (reduced from $35-50/month)

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1" # Ireland - closest to Portugal
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "fiscaliza.pt"
}

# Cost Optimization Mode
variable "cost_optimization_mode" {
  description = "Enable aggressive cost optimization mode"
  type        = bool
  default     = true
}

# Database Configuration - Standard RDS PostgreSQL
variable "db_engine" {
  description = "Database engine (postgresql for cost optimization)"
  type        = string
  default     = "postgres"
  validation {
    condition     = var.db_engine == "postgres"
    error_message = "Only PostgreSQL is supported in cost optimization mode."
  }
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
  validation {
    condition     = var.db_instance_class == "db.t4g.micro"
    error_message = "Only db.t4g.micro is supported for cost optimization."
  }
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS (GB)"
  type        = number
  default     = 20
  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 100
    error_message = "Storage must be between 20 and 100 GB for cost optimization."
  }
}

variable "db_storage_type" {
  description = "Storage type for RDS"
  type        = string
  default     = "gp3"
  validation {
    condition     = contains(["gp3", "gp2"], var.db_storage_type)
    error_message = "Only gp3 or gp2 storage types are supported."
  }
}

variable "db_backup_retention_period" {
  description = "Backup retention period (days)"
  type        = number
  default     = 1
  validation {
    condition     = var.db_backup_retention_period >= 1 && var.db_backup_retention_period <= 7
    error_message = "Backup retention must be between 1 and 7 days for cost optimization."
  }
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false # Single AZ for cost optimization
}

# Lambda Configuration - Optimized
variable "lambda_memory_size" {
  description = "Memory size for Lambda function (MB)"
  type        = number
  default     = 512
  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 1024
    error_message = "Lambda memory size must be between 128 MB and 1024 MB for cost optimization."
  }
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function (seconds)"
  type        = number
  default     = 30
  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 300
    error_message = "Lambda timeout must be between 1 and 300 seconds."
  }
}

variable "lambda_reserved_concurrency" {
  description = "Reserved concurrency for Lambda (free up to 1000)"
  type        = number
  default     = 10
  validation {
    condition     = var.lambda_reserved_concurrency >= 0 && var.lambda_reserved_concurrency <= 100
    error_message = "Reserved concurrency must be between 0 and 100."
  }
}

variable "lambda_use_function_url" {
  description = "Use Lambda Function URL instead of API Gateway"
  type        = bool
  default     = true # Cost optimization
}

# Cloudflare Configuration
variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID for fiscaliza.pt"
  type        = string
  default     = ""
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token"
  type        = string
  sensitive   = true
  default     = ""
}

variable "enable_cloudflare_cache" {
  description = "Enable Cloudflare caching rules"
  type        = bool
  default     = true
}

variable "enable_cloudflare_waf" {
  description = "Enable Cloudflare WAF rules"
  type        = bool
  default     = true
}

variable "cloudflare_cache_level" {
  description = "Cloudflare cache level"
  type        = string
  default     = "aggressive"
  validation {
    condition     = contains(["basic", "simplified", "aggressive"], var.cloudflare_cache_level)
    error_message = "Cache level must be basic, simplified, or aggressive."
  }
}

variable "create_api_subdomain" {
  description = "Create api subdomain for Cloudflare"
  type        = bool
  default     = false
}

# CloudFront Configuration - Simplified for S3 only
variable "enable_cloudfront" {
  description = "Enable CloudFront for S3 static assets"
  type        = bool
  default     = true
}

variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100" # US, Canada, Europe only
  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.cloudfront_price_class)
    error_message = "CloudFront price class must be PriceClass_100, PriceClass_200, or PriceClass_All."
  }
}

# Monitoring Configuration - Minimal
variable "enable_basic_monitoring" {
  description = "Enable basic CloudWatch monitoring"
  type        = bool
  default     = true
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring (costs extra)"
  type        = bool
  default     = false # Disabled for cost optimization
}

variable "alert_email" {
  description = "Email address for critical alerts"
  type        = string
  default     = ""
  validation {
    condition     = var.alert_email == "" || can(regex("^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$", var.alert_email))
    error_message = "Alert email must be a valid email address or empty string."
  }
}

# Disabled Services for Cost Optimization
variable "enable_redis_cache" {
  description = "Enable ElastiCache Redis (DISABLED for cost optimization)"
  type        = bool
  default     = false
}

variable "lambda_provisioned_concurrency" {
  description = "Provisioned concurrency (DISABLED for cost optimization)"
  type        = number
  default     = 0
}

variable "enable_backup_service" {
  description = "Enable AWS Backup service (DISABLED for cost optimization)"
  type        = bool
  default     = false
}

variable "enable_guardduty" {
  description = "Enable AWS GuardDuty (DISABLED for cost optimization)"
  type        = bool
  default     = false
}

variable "enable_security_hub" {
  description = "Enable AWS Security Hub (DISABLED for cost optimization)"
  type        = bool
  default     = false
}

variable "enable_xray_tracing" {
  description = "Enable AWS X-Ray tracing (DISABLED for cost optimization)"
  type        = bool
  default     = false
}

variable "enable_synthetics" {
  description = "Enable CloudWatch Synthetics (DISABLED for cost optimization)"
  type        = bool
  default     = false
}

variable "enable_enhanced_waf" {
  description = "Enable enhanced WAF (DISABLED for cost optimization)"
  type        = bool
  default     = false
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup (DISABLED for cost optimization)"
  type        = bool
  default     = false
}

# Application Caching Configuration
variable "enable_in_memory_cache" {
  description = "Enable in-memory caching in Lambda"
  type        = bool
  default     = true
}

variable "cache_ttl_seconds" {
  description = "Default cache TTL in seconds"
  type        = number
  default     = 300
}

variable "enable_connection_pooling" {
  description = "Enable database connection pooling"
  type        = bool
  default     = true
}

variable "max_connections" {
  description = "Maximum database connections"
  type        = number
  default     = 5
  validation {
    condition     = var.max_connections >= 1 && var.max_connections <= 20
    error_message = "Max connections must be between 1 and 20."
  }
}

variable "backend_image" {
  description = "Docker image URI for the backend Lambda function"
  type        = string
  default     = ""
}

# Migration Configuration
variable "migrate_from_aurora" {
  description = "Enable migration mode from Aurora to PostgreSQL"
  type        = bool
  default     = false
}

variable "preserve_aurora_during_migration" {
  description = "Keep Aurora running during migration"
  type        = bool
  default     = false
}