# VPC Endpoints for Cost Optimization and Security
# Reduces NAT Gateway costs by ~$30/month and improves security

# Variable to control VPC endpoints
variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for enhanced security and cost optimization"
  type        = bool
  default     = true
}

# Security Group for Interface VPC Endpoints
resource "aws_security_group" "vpc_endpoints" {
  count = var.enable_vpc_endpoints ? 1 : 0

  name_prefix = "${local.name_prefix}-vpc-endpoints-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for VPC endpoints"

  ingress {
    description = "HTTPS from private subnets"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-vpc-endpoints-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# 1. S3 VPC Endpoint (Gateway Type - FREE)
resource "aws_vpc_endpoint" "s3" {
  count = var.enable_vpc_endpoints ? 1 : 0

  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = aws_route_table.private[*].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.frontend.arn,
          "${aws_s3_bucket.frontend.arn}/*"
        ]
      }
    ]
  })

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-s3-endpoint"
  })
}

# 2. Secrets Manager VPC Endpoint (Interface Type)
resource "aws_vpc_endpoint" "secrets_manager" {
  count = var.enable_vpc_endpoints ? 1 : 0

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:PrincipalArn" = [
              var.deployment_type == "serverless" ? aws_iam_role.lambda_execution[0].arn : null,
              var.deployment_type == "fargate" ? aws_iam_role.ecs_task[0].arn : null
            ]
          }
        }
      }
    ]
  })

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-secrets-manager-endpoint"
  })
}

# 3. CloudWatch Logs VPC Endpoint (Interface Type)
resource "aws_vpc_endpoint" "logs" {
  count = var.enable_vpc_endpoints ? 1 : 0

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.logs"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = "*"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-cloudwatch-logs-endpoint"
  })
}

# 4. ECR VPC Endpoints (for Docker image pulls)
resource "aws_vpc_endpoint" "ecr_dkr" {
  count = var.enable_vpc_endpoints ? 1 : 0

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-ecr-dkr-endpoint"
  })
}

resource "aws_vpc_endpoint" "ecr_api" {
  count = var.enable_vpc_endpoints ? 1 : 0

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-ecr-api-endpoint"
  })
}

# 5. RDS VPC Endpoint (for Aurora management API calls)
resource "aws_vpc_endpoint" "rds" {
  count = var.enable_vpc_endpoints && var.deployment_type == "serverless" ? 1 : 0

  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.aws_region}.rds"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints[0].id]
  private_dns_enabled = true

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-rds-endpoint"
  })
}

# Output VPC endpoint information
output "vpc_endpoints_enabled" {
  description = "Whether VPC endpoints are enabled"
  value       = var.enable_vpc_endpoints
}

output "vpc_endpoint_cost_savings" {
  description = "Estimated monthly cost savings from VPC endpoints"
  value       = var.enable_vpc_endpoints ? "~$25-35/month savings vs NAT Gateway for typical traffic" : "VPC endpoints disabled"
}

output "vpc_endpoints_created" {
  description = "List of VPC endpoints created"
  value = var.enable_vpc_endpoints ? [
    "S3 Gateway (FREE)",
    "Secrets Manager Interface (~$7/month)",
    "CloudWatch Logs Interface (~$7/month)",
    "ECR API Interface (~$7/month)",
    "ECR Docker Interface (~$7/month)",
    var.deployment_type == "serverless" ? "RDS Interface (~$7/month)" : null
  ] : []
}