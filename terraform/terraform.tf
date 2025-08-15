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

  # Remote state configuration (uncomment and configure as needed)
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "parliament/terraform.tfstate"
  #   region         = "eu-west-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

# Cloudflare provider configuration
provider "cloudflare" {
  api_token = var.cloudflare_api_token
}