# Database Module
# Provides Aurora Serverless v2 with enhanced configuration, ElastiCache Redis, and backups

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "lambda_security_group_id" {
  description = "Lambda security group ID"
  type        = string
}

variable "aurora_min_capacity" {
  description = "Aurora min capacity"
  type        = number
  default     = 0.5
}

variable "aurora_max_capacity" {
  description = "Aurora max capacity"
  type        = number
  default     = 8
}

variable "backup_retention_days" {
  description = "Backup retention days"
  type        = number
  default     = 30
}

variable "enable_redis_cache" {
  description = "Enable Redis cache"
  type        = bool
  default     = true
}

variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# KMS Key for Aurora encryption
resource "aws_kms_key" "aurora" {
  description             = "KMS key for Aurora cluster encryption"
  deletion_window_in_days = 7
  tags                    = var.tags
}

resource "aws_kms_alias" "aurora" {
  name          = "alias/${local.name_prefix}-aurora"
  target_key_id = aws_kms_key.aurora.key_id
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = var.private_subnet_ids
  tags       = merge(var.tags, { Name = "${local.name_prefix}-db-subnet-group" })
}

# Security Group for Aurora
resource "aws_security_group" "aurora" {
  name_prefix = "${local.name_prefix}-aurora-"
  vpc_id      = var.vpc_id
  description = "Security group for Aurora cluster"

  ingress {
    description     = "MySQL from Lambda"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [var.lambda_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${local.name_prefix}-aurora-sg" })

  lifecycle {
    create_before_destroy = true
  }
}

# Aurora Serverless v2 Cluster
resource "aws_rds_cluster" "main" {
  cluster_identifier = "${local.name_prefix}-aurora"
  engine             = "aurora-mysql"
  engine_mode        = "provisioned"
  engine_version     = "8.0.mysql_aurora.3.07.0"
  database_name      = "parliament"
  master_username    = "admin"

  manage_master_user_password = true

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.aurora.id]

  # Enhanced backup configuration
  backup_retention_period      = var.backup_retention_days
  preferred_backup_window      = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"

  # Point-in-time recovery with enhanced retention
  copy_tags_to_snapshot = true

  # Enhanced backup features
  enabled_cloudwatch_logs_exports = ["error", "general", "slowquery", "audit"]

  # Serverless v2 scaling configuration
  serverlessv2_scaling_configuration {
    max_capacity = var.aurora_max_capacity
    min_capacity = var.aurora_min_capacity
  }

  # Security
  storage_encrypted = true
  kms_key_id        = aws_kms_key.aurora.arn

  # Enhanced Performance Insights configuration
  performance_insights_enabled          = true
  performance_insights_retention_period = 7

  # Deletion protection for production
  deletion_protection      = var.environment == "prod" ? true : false
  skip_final_snapshot      = var.environment == "prod" ? false : true
  final_snapshot_identifier = var.environment == "prod" ? "${local.name_prefix}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  tags = merge(var.tags, { Name = "${local.name_prefix}-aurora-cluster" })
}

# Aurora Serverless v2 Instance
resource "aws_rds_cluster_instance" "main" {
  identifier         = "${local.name_prefix}-aurora-instance"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  # Performance monitoring
  performance_insights_enabled = true
  monitoring_interval          = 60
  monitoring_role_arn          = aws_iam_role.rds_monitoring.arn

  tags = merge(var.tags, { Name = "${local.name_prefix}-aurora-instance" })
}

# IAM Role for RDS Monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${local.name_prefix}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.tags, { Name = "${local.name_prefix}-rds-monitoring-role" })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# ElastiCache Resources (conditionally created)
resource "aws_elasticache_subnet_group" "main" {
  count = var.enable_redis_cache ? 1 : 0

  name       = "${local.name_prefix}-redis-subnet-group"
  subnet_ids = var.private_subnet_ids
  tags       = merge(var.tags, { Name = "${local.name_prefix}-redis-subnet-group" })
}

resource "aws_security_group" "redis" {
  count = var.enable_redis_cache ? 1 : 0

  name_prefix = "${local.name_prefix}-redis-"
  vpc_id      = var.vpc_id
  description = "Security group for ElastiCache Redis"

  ingress {
    description     = "Redis from Lambda"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.lambda_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${local.name_prefix}-redis-sg" })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_elasticache_parameter_group" "main" {
  count = var.enable_redis_cache ? 1 : 0

  family = "redis7.x"
  name   = "${local.name_prefix}-redis-params"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  tags = merge(var.tags, { Name = "${local.name_prefix}-redis-params" })
}

resource "aws_elasticache_replication_group" "main" {
  count = var.enable_redis_cache ? 1 : 0

  replication_group_id = "${local.name_prefix}-redis"
  description          = "Redis cluster for Parliament application caching"

  node_type            = var.redis_node_type
  port                 = 6379
  parameter_group_name = aws_elasticache_parameter_group.main[0].name

  num_cache_clusters         = var.environment == "prod" ? 2 : 1
  automatic_failover_enabled = var.environment == "prod" ? true : false
  multi_az_enabled          = var.environment == "prod" ? true : false

  subnet_group_name  = aws_elasticache_subnet_group.main[0].name
  security_group_ids = [aws_security_group.redis[0].id]

  snapshot_retention_limit = var.environment == "prod" ? 5 : 1
  snapshot_window         = "02:00-03:00"
  maintenance_window      = "sun:03:00-sun:04:00"

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = random_password.redis_auth[0].result

  apply_immediately = false

  tags = merge(var.tags, { Name = "${local.name_prefix}-redis-cluster" })
}

resource "random_password" "redis_auth" {
  count = var.enable_redis_cache ? 1 : 0

  length  = 32
  special = true
}

# Secrets Manager for Redis Auth
resource "aws_secretsmanager_secret" "redis_auth" {
  count = var.enable_redis_cache ? 1 : 0

  name                    = "${local.name_prefix}-redis-auth"
  description             = "Redis authentication token"
  recovery_window_in_days = 7
  tags                    = merge(var.tags, { Name = "${local.name_prefix}-redis-auth" })
}

resource "aws_secretsmanager_secret_version" "redis_auth" {
  count = var.enable_redis_cache ? 1 : 0

  secret_id = aws_secretsmanager_secret.redis_auth[0].id
  secret_string = jsonencode({
    auth_token = random_password.redis_auth[0].result
    endpoint   = aws_elasticache_replication_group.main[0].primary_endpoint_address
    port       = aws_elasticache_replication_group.main[0].port
  })
}

# Outputs
output "aurora_cluster_arn" {
  description = "Aurora cluster ARN"
  value       = aws_rds_cluster.main.arn
}

output "aurora_cluster_id" {
  description = "Aurora cluster identifier"
  value       = aws_rds_cluster.main.cluster_identifier
}

output "aurora_endpoint" {
  description = "Aurora cluster endpoint"
  value       = aws_rds_cluster.main.endpoint
}

output "aurora_master_user_secret_arn" {
  description = "Aurora master user secret ARN"
  value       = aws_rds_cluster.main.master_user_secret[0].secret_arn
}

output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = var.enable_redis_cache ? aws_elasticache_replication_group.main[0].primary_endpoint_address : null
}

output "redis_auth_secret_arn" {
  description = "Redis authentication secret ARN"
  value       = var.enable_redis_cache ? aws_secretsmanager_secret.redis_auth[0].arn : null
}

output "redis_cluster_id" {
  description = "Redis cluster ID"
  value       = var.enable_redis_cache ? aws_elasticache_replication_group.main[0].replication_group_id : null
}