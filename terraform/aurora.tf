# Aurora Serverless v2 Cluster
resource "aws_rds_cluster" "parliament" {

  cluster_identifier        = "${local.name_prefix}-aurora"
  engine                   = "aurora-mysql"
  engine_mode              = "provisioned"
  engine_version           = "8.0.mysql_aurora.3.07.0"
  database_name            = "parliament"
  master_username          = "admin"
  manage_master_user_password = true
  
  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.parliament.name
  vpc_security_group_ids = [aws_security_group.aurora.id]
  
  # Backup configuration (environment-specific)
  backup_retention_period = var.environment == "prod" ? 7 : 1
  preferred_backup_window = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"
  
  # Point-in-time recovery (production only)
  copy_tags_to_snapshot = true
  backup_retention_period_s3 = var.environment == "prod" ? 30 : 0
  
  # Serverless v2 scaling configuration
  serverlessv2_scaling_configuration {
    max_capacity = var.aurora_max_capacity
    min_capacity = var.aurora_min_capacity
  }
  
  # Security
  storage_encrypted = true
  kms_key_id       = aws_kms_key.aurora.arn
  
  # Performance Insights
  enabled_cloudwatch_logs_exports = ["error", "general", "slowquery"]
  
  # Deletion protection for production
  deletion_protection = var.environment == "prod" ? true : false
  skip_final_snapshot = var.environment == "prod" ? false : true
  final_snapshot_identifier = var.environment == "prod" ? "${local.name_prefix}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null
  
  # Copy tags to snapshots
  copy_tags_to_snapshot = true
  
  tags = merge(local.tags, {
    Name = "${local.name_prefix}-aurora-cluster"
  })
}

# Aurora Serverless v2 Instance
resource "aws_rds_cluster_instance" "parliament" {
  identifier         = "${local.name_prefix}-aurora-instance"
  cluster_identifier = aws_rds_cluster.parliament.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.parliament.engine
  engine_version     = aws_rds_cluster.parliament.engine_version
  
  # Performance monitoring
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn
  
  tags = merge(local.tags, {
    Name = "${local.name_prefix}-aurora-instance"
  })
}

# DB Subnet Group
resource "aws_db_subnet_group" "parliament" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}

# Security Group for Aurora
resource "aws_security_group" "aurora" {

  name_prefix = "${local.name_prefix}-aurora-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for Aurora cluster"

  ingress {
    description     = "MySQL from Lambda"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-aurora-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# KMS Key for Aurora encryption
resource "aws_kms_key" "aurora" {

  description             = "KMS key for Aurora cluster encryption"
  deletion_window_in_days = 7

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-aurora-kms"
  })
}

resource "aws_kms_alias" "aurora" {
  name          = "alias/${local.name_prefix}-aurora"
  target_key_id = aws_kms_key.aurora.key_id
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

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-rds-monitoring-role"
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Lambda IAM policy for Aurora access
resource "aws_iam_role_policy" "lambda_aurora_access" {
  name = "${local.name_prefix}-lambda-aurora-access"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds-data:BatchExecuteStatement",
          "rds-data:BeginTransaction",
          "rds-data:CommitTransaction",
          "rds-data:ExecuteStatement",
          "rds-data:RollbackTransaction"
        ]
        Resource = aws_rds_cluster.parliament.arn
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_rds_cluster.parliament.master_user_secret[0].secret_arn
      }
    ]
  })
}

# CloudWatch Alarms for Aurora
resource "aws_cloudwatch_metric_alarm" "aurora_cpu" {

  alarm_name          = "${local.name_prefix}-aurora-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors Aurora CPU utilization"

  dimensions = {
    DBClusterIdentifier = aws_rds_cluster.parliament.cluster_identifier
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-aurora-cpu-alarm"
  })
}

resource "aws_cloudwatch_metric_alarm" "aurora_connections" {

  alarm_name          = "${local.name_prefix}-aurora-high-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "40"  # 80% of default max_connections for serverless
  alarm_description   = "This metric monitors Aurora connection count"

  dimensions = {
    DBClusterIdentifier = aws_rds_cluster.parliament.cluster_identifier
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-aurora-connections-alarm"
  })
}