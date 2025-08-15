# Portuguese Parliament Transparency Platform - Main Configuration
# Fiscaliza.pt - Cost-optimized architecture with PostgreSQL RDS and Lambda Function URL
# Target cost: $11-17/month

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# Local values
locals {
  name_prefix = "fiscaliza-${var.environment}"

  tags = {
    Project       = "Fiscaliza"
    Environment   = var.environment
    ManagedBy     = "Terraform"
    Website       = "fiscaliza.pt"
    CostOptimized = "true"
    TargetCost    = "$11-17/month"
  }

  # Calculate number of availability zones (minimum 2 for redundancy)
  azs = slice(data.aws_availability_zones.available.names, 0, 2)
}

# VPC for cost-optimized infrastructure
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-igw"
  })
}

# Public subnets (for NAT Gateway)
resource "aws_subnet" "public" {
  count = length(local.azs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-public-${count.index + 1}"
    Type = "Public"
  })
}

# Private subnets (for Lambda and RDS)
resource "aws_subnet" "private" {
  count = length(local.azs)

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = local.azs[count.index]

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-private-${count.index + 1}"
    Type = "Private"
  })
}

# Single NAT Gateway for cost optimization (instead of one per AZ)
resource "aws_eip" "nat" {
  domain = "vpc"

  depends_on = [aws_internet_gateway.main]

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-nat-eip"
  })
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  depends_on = [aws_internet_gateway.main]

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-nat"
  })
}

# Route table for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-public-rt"
  })
}

# Route table for private subnets
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-private-rt"
  })
}

# Route table associations
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# VPC Endpoints for cost optimization (reduce NAT Gateway usage)
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.${var.aws_region}.s3"

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-s3-endpoint"
  })
}

resource "aws_vpc_endpoint_route_table_association" "s3_private" {
  route_table_id  = aws_route_table.private.id
  vpc_endpoint_id = aws_vpc_endpoint.s3.id
}

# VPC Flow Logs (basic, cost-optimized)
resource "aws_flow_log" "vpc" {
  count = var.enable_basic_monitoring ? 1 : 0

  iam_role_arn    = aws_iam_role.flow_logs[0].arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs[0].arn
  traffic_type    = "REJECT" # Only log rejected traffic for security
  vpc_id          = aws_vpc.main.id

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-vpc-flow-logs"
  })
}

resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  count = var.enable_basic_monitoring ? 1 : 0

  name              = "/aws/vpc/flowlogs/${local.name_prefix}"
  retention_in_days = 3 # Short retention for cost optimization

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-vpc-flow-logs"
  })
}

resource "aws_iam_role" "flow_logs" {
  count = var.enable_basic_monitoring ? 1 : 0

  name = "${local.name_prefix}-flow-logs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-flow-logs-role"
  })
}

resource "aws_iam_role_policy" "flow_logs" {
  count = var.enable_basic_monitoring ? 1 : 0

  name = "${local.name_prefix}-flow-logs-policy"
  role = aws_iam_role.flow_logs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# Basic security group for VPC endpoints
resource "aws_security_group" "vpc_endpoints" {
  name_prefix = "${local.name_prefix}-vpc-endpoints-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for VPC endpoints"

  ingress {
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