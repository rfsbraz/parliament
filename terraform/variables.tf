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
  default     = 10
  validation {
    condition     = var.max_connections >= 6 && var.max_connections <= 20
    error_message = "Max connections must be between 6 and 20 (PostgreSQL minimum is 6)."
  }
}

variable "backend_image" {
  description = "Docker image URI for the backend Lambda function"
  type        = string
  default     = ""
}

# ============================================================================
# TAGGING CONFIGURATION FOR COST ANALYSIS AND RESOURCE MANAGEMENT
# ============================================================================

variable "project_name" {
  description = "Project name for tagging and identification"
  type        = string
  default     = "Parliament"
  validation {
    condition     = length(var.project_name) > 0 && length(var.project_name) <= 50
    error_message = "Project name must be between 1 and 50 characters."
  }
}

variable "application_name" {
  description = "Application name for tagging"
  type        = string
  default     = "Fiscaliza"
  validation {
    condition     = length(var.application_name) > 0 && length(var.application_name) <= 50
    error_message = "Application name must be between 1 and 50 characters."
  }
}

variable "cost_center" {
  description = "Cost center for billing allocation"
  type        = string
  default     = "Parliament-Analytics"
  validation {
    condition     = length(var.cost_center) > 0 && length(var.cost_center) <= 100
    error_message = "Cost center must be between 1 and 100 characters."
  }
}

variable "owner_team" {
  description = "Team responsible for the resources"
  type        = string
  default     = "DevOps"
  validation {
    condition     = length(var.owner_team) > 0 && length(var.owner_team) <= 50
    error_message = "Owner team must be between 1 and 50 characters."
  }
}

variable "owner_email" {
  description = "Email of the resource owner for contact purposes"
  type        = string
  default     = ""
  validation {
    condition     = var.owner_email == "" || can(regex("^[\\w\\.-]+@[\\w\\.-]+\\.[a-zA-Z]{2,}$", var.owner_email))
    error_message = "Owner email must be a valid email address or empty string."
  }
}

variable "business_unit" {
  description = "Business unit responsible for costs"
  type        = string
  default     = "Government-Transparency"
  validation {
    condition     = length(var.business_unit) > 0 && length(var.business_unit) <= 100
    error_message = "Business unit must be between 1 and 100 characters."
  }
}

variable "backup_schedule" {
  description = "Backup schedule for resources (daily, weekly, monthly, none)"
  type        = string
  default     = "daily"
  validation {
    condition     = contains(["daily", "weekly", "monthly", "none"], var.backup_schedule)
    error_message = "Backup schedule must be one of: daily, weekly, monthly, none."
  }
}

variable "data_classification" {
  description = "Data classification level (public, internal, confidential, restricted)"
  type        = string
  default     = "public"
  validation {
    condition     = contains(["public", "internal", "confidential", "restricted"], var.data_classification)
    error_message = "Data classification must be one of: public, internal, confidential, restricted."
  }
}

variable "compliance_requirements" {
  description = "Compliance requirements (gdpr, none, custom)"
  type        = string
  default     = "gdpr"
  validation {
    condition     = contains(["gdpr", "none", "custom"], var.compliance_requirements)
    error_message = "Compliance requirements must be one of: gdpr, none, custom."
  }
}

variable "auto_shutdown" {
  description = "Whether resources support auto-shutdown for cost optimization"
  type        = bool
  default     = false
}

variable "monitoring_level" {
  description = "Level of monitoring required (basic, standard, enhanced)"
  type        = string
  default     = "basic"
  validation {
    condition     = contains(["basic", "standard", "enhanced"], var.monitoring_level)
    error_message = "Monitoring level must be one of: basic, standard, enhanced."
  }
}

variable "additional_tags" {
  description = "Additional custom tags to apply to all resources"
  type        = map(string)
  default     = {}
  validation {
    condition     = length(var.additional_tags) <= 10
    error_message = "Additional tags cannot exceed 10 key-value pairs."
  }
}

# ============================================================================
# AUTOMATED DATA IMPORT CONFIGURATION
# ============================================================================
# Ultra-cost-effective spot instance based automated data import
# Total additional cost: ~$0.03/month for daily 20-minute imports

variable "enable_automated_import" {
  description = "Enable automated parliament data import using spot instances"
  type        = bool
  default     = true
}

# Import-related variables are defined in spot-import-variables.tf

# Remote Database Access
variable "admin_ip_address" {
  description = "IP address allowed for remote database access (your current IP)"
  type        = string
  default     = ""
  validation {
    condition     = var.admin_ip_address == "" || can(regex("^[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}$", var.admin_ip_address))
    error_message = "Admin IP address must be a valid IPv4 address or empty string."
  }
}

