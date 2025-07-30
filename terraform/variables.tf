variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-1"  # Ireland - closest to Portugal
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "domain_name" {
  description = "Domain name for the application (optional)"
  type        = string
  default     = ""
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS (optional)"
  type        = string
  default     = ""
}


# Backend configuration
variable "backend_image" {
  description = "Docker image for the Lambda backend"
  type        = string
  default     = "parliament-backend:latest"
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda function (MB)"
  type        = number
  default     = 1024
  validation {
    condition     = var.lambda_memory_size >= 128 && var.lambda_memory_size <= 10240
    error_message = "Lambda memory size must be between 128 MB and 10,240 MB."
  }
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function (seconds)"
  type        = number
  default     = 30
  validation {
    condition     = var.lambda_timeout >= 1 && var.lambda_timeout <= 900
    error_message = "Lambda timeout must be between 1 and 900 seconds."
  }
}

variable "lambda_vpc_enabled" {
  description = "Enable VPC configuration for Lambda function"
  type        = bool
  default     = true  # Required for Aurora access
}

# Remote state management variables
variable "create_cicd_user" {
  description = "Create IAM user for CI/CD pipeline access to Terraform state"
  type        = bool
  default     = false
}

# Aurora Serverless v2 variables
variable "aurora_min_capacity" {
  description = "Minimum Aurora Serverless v2 capacity (ACUs)"
  type        = number
  default     = 0.5
  validation {
    condition     = var.aurora_min_capacity >= 0.5 && var.aurora_min_capacity <= 128
    error_message = "Aurora min capacity must be between 0.5 and 128 ACUs."
  }
}

variable "aurora_max_capacity" {
  description = "Maximum Aurora Serverless v2 capacity (ACUs)"
  type        = number
  default     = 2
  validation {
    condition     = var.aurora_max_capacity >= 0.5 && var.aurora_max_capacity <= 128
    error_message = "Aurora max capacity must be between 0.5 and 128 ACUs."
  }
}