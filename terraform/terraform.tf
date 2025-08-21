# Terraform Configuration for Portuguese Parliament Transparency Application
# Cost-Optimized Infrastructure with PostgreSQL RDS and Lambda Function URL

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }

  # Remote state configuration
  backend "s3" {
    bucket         = "parliament-terraform-state-eu-west-1"
    key            = "terraform.tfstate"
    region         = "eu-west-1"
    profile        = "reddit-proxy"
    encrypt        = true
    dynamodb_table = "parliament-terraform-locks"
  }
}

# AWS provider configuration
provider "aws" {
  profile = "reddit-proxy"
  region = var.aws_region

  # Default tags applied to all AWS resources
  default_tags {
    tags = {
      Project              = var.project_name
      Application          = var.application_name
      Environment          = var.environment
      ManagedBy           = "Terraform"
      BusinessUnit        = var.business_unit
      CostCenter          = var.cost_center
      OwnerTeam           = var.owner_team
      OwnerEmail          = var.owner_email
      DataClassification  = var.data_classification
      ComplianceRequirements = var.compliance_requirements
      BackupSchedule      = var.backup_schedule
      MonitoringLevel     = var.monitoring_level
      AutoShutdown        = var.auto_shutdown ? "enabled" : "disabled"
      CostOptimized       = var.cost_optimization_mode ? "true" : "false"
      CreatedDate         = formatdate("YYYY-MM-DD", timestamp())
      Terraform           = "true"
      Repository          = "parliament"
    }
  }
}

# Cloudflare provider configuration
provider "cloudflare" {
  api_token = var.cloudflare_api_token
  # Alternative: use email + api_key for full access
  # email   = "your-email@example.com"
  # api_key = var.cloudflare_api_key
}