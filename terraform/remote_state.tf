# Terraform Remote State Management
# This file sets up S3 backend for Terraform state storage with DynamoDB locking

# S3 Bucket for Terraform State
resource "aws_s3_bucket" "terraform_state" {
  bucket = "${local.name_prefix}-terraform-state-${random_string.state_suffix.result}"

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-terraform-state"
    Purpose = "Terraform state storage"
  })
}

resource "random_string" "state_suffix" {
  length  = 8
  special = false
  upper   = false
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Server Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    id     = "terraform_state_lifecycle"
    status = "Enabled"

    # Keep non-current versions for 30 days
    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    # Move to IA after 30 days
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Move to Glacier after 90 days
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

# DynamoDB Table for State Locking
resource "aws_dynamodb_table" "terraform_locks" {
  name           = "${local.name_prefix}-terraform-locks"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-terraform-locks"
    Purpose = "Terraform state locking"
  })
}

# IAM Policy for Terraform State Access
resource "aws_iam_policy" "terraform_state" {
  name        = "${local.name_prefix}-terraform-state-policy"
  description = "IAM policy for Terraform state management"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:GetBucketVersioning"
        ]
        Resource = aws_s3_bucket.terraform_state.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObjectVersion"
        ]
        Resource = "${aws_s3_bucket.terraform_state.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = aws_dynamodb_table.terraform_locks.arn
      }
    ]
  })

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-terraform-state-policy"
  })
}

# IAM User for CI/CD (if needed)
resource "aws_iam_user" "terraform_cicd" {
  count = var.create_cicd_user ? 1 : 0
  name  = "${local.name_prefix}-terraform-cicd"

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-terraform-cicd-user"
    Purpose = "CI/CD Terraform deployments"
  })
}

resource "aws_iam_user_policy_attachment" "terraform_cicd" {
  count      = var.create_cicd_user ? 1 : 0
  user       = aws_iam_user.terraform_cicd[0].name
  policy_arn = aws_iam_policy.terraform_state.arn
}

# Generate backend configuration
resource "local_file" "backend_config" {
  content = templatefile("${path.module}/templates/backend.tf.tpl", {
    bucket         = aws_s3_bucket.terraform_state.bucket
    key            = "${var.environment}/${var.deployment_type}/terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = aws_dynamodb_table.terraform_locks.name
    encrypt        = true
  })
  filename = "${path.module}/generated_backend_${var.environment}_${var.deployment_type}.tf"

  depends_on = [
    aws_s3_bucket.terraform_state,
    aws_dynamodb_table.terraform_locks
  ]
}

# Output remote state information
output "terraform_state_bucket" {
  description = "S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.bucket
}

output "terraform_locks_table" {
  description = "DynamoDB table for Terraform state locking"
  value       = aws_dynamodb_table.terraform_locks.name
}

output "backend_configuration" {
  description = "Terraform backend configuration"
  value = {
    bucket         = aws_s3_bucket.terraform_state.bucket
    key            = "${var.environment}/${var.deployment_type}/terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = aws_dynamodb_table.terraform_locks.name
    encrypt        = true
  }
}

output "remote_state_setup_commands" {
  description = "Commands to initialize remote state"
  value = [
    "# 1. Initialize with remote state:",
    "terraform init -backend-config=\"bucket=${aws_s3_bucket.terraform_state.bucket}\" -backend-config=\"key=${var.environment}/${var.deployment_type}/terraform.tfstate\" -backend-config=\"region=${var.aws_region}\" -backend-config=\"dynamodb_table=${aws_dynamodb_table.terraform_locks.name}\"",
    "",
    "# 2. Or copy the generated backend configuration file:",
    "cp generated_backend_${var.environment}_${var.deployment_type}.tf backend.tf",
    "terraform init",
    "",
    "# 3. Migrate existing state (if any):",
    "terraform init -migrate-state"
  ]
}