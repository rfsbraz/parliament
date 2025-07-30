# Security Group for Application Load Balancer (only for Fargate deployment)
resource "aws_security_group" "alb" {
  count = var.deployment_type == "fargate" ? 1 : 0
  name        = "${local.name_prefix}-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-alb-sg"
  })
}

# Security Group for Backend ECS Tasks (only for Fargate deployment)
resource "aws_security_group" "backend" {
  count = var.deployment_type == "fargate" ? 1 : 0
  name        = "${local.name_prefix}-backend-sg"
  description = "Security group for backend ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "HTTP from ALB"
    from_port       = 5000
    to_port         = 5000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb[0].id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-backend-sg"
  })
}

# Security Group for EFS (if database persistence is enabled)
resource "aws_security_group" "efs" {
  count = var.enable_database_persistence ? 1 : 0

  name        = "${local.name_prefix}-efs-sg"
  description = "Security group for EFS file system"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "NFS from backend"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.backend[0].id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-efs-sg"
  })
}

# IAM Role for ECS Task Execution (only for Fargate deployment)
resource "aws_iam_role" "ecs_execution" {
  count = var.deployment_type == "fargate" ? 1 : 0
  name = "${local.name_prefix}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-ecs-execution-role"
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  count = var.deployment_type == "fargate" ? 1 : 0
  role       = aws_iam_role.ecs_execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# IAM Role for ECS Tasks (only for Fargate deployment)
resource "aws_iam_role" "ecs_task" {
  count = var.deployment_type == "fargate" ? 1 : 0
  name = "${local.name_prefix}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-ecs-task-role"
  })
}

# EFS permissions for ECS tasks (if database persistence is enabled)
resource "aws_iam_role_policy" "efs_access" {
  count = var.enable_database_persistence ? 1 : 0

  name = "${local.name_prefix}-efs-access"
  role = aws_iam_role.ecs_task[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticfilesystem:*"
        ]
        Resource = "*"
      }
    ]
  })
}