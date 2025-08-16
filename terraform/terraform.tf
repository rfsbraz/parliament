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
  # NOTE: Backend configuration cannot use variables
  # Use different key paths for different environments:
  # - Dev:  terraform init -backend-config="key=dev/terraform.tfstate"
  # - Prod: terraform init -backend-config="key=prod/terraform.tfstate"
  backend "s3" {
    bucket         = "parliament-terraform-state-eu-west-1"
    key            = "terraform.tfstate"  # Override this during init
    region         = "eu-west-1"
    encrypt        = true
    dynamodb_table = "parliament-terraform-locks"
    
    # Additional security settings
    kms_key_id = "alias/terraform-state-key"
  }
}

# Cloudflare provider configuration
provider "cloudflare" {
  api_token = var.cloudflare_api_token
}