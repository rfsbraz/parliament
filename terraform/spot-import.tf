# Spot Instance Import Infrastructure
# Ultra-cost-effective automated data import using spot instances (~$0.03/month)

# ============================================================================
# DATA SOURCES
# ============================================================================

# Latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ============================================================================
# LAMBDA FUNCTION FOR SPOT INSTANCE LAUNCHER
# ============================================================================

# Archive for Lambda function code
data "archive_file" "spot_launcher" {
  type        = "zip"
  output_path = "spot_launcher.zip"
  source {
    content = <<EOF
import json
import boto3
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ec2_client = boto3.client('ec2')
logs_client = boto3.client('logs')

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda function to launch spot instances for parliament data import.
    Supports both EventBridge scheduled triggers and manual Function URL calls.
    """
    
    try:
        # Get configuration from environment variables
        instance_type = os.environ.get('SPOT_INSTANCE_TYPE', 't3.nano')
        subnet_ids = os.environ.get('PRIVATE_SUBNET_IDS', '').split(',')
        security_group_id = os.environ.get('SECURITY_GROUP_ID', '')
        iam_instance_profile = os.environ.get('IAM_INSTANCE_PROFILE', '')
        max_price = os.environ.get('SPOT_MAX_PRICE', '')
        timeout_minutes = int(os.environ.get('IMPORT_TIMEOUT_MINUTES', '30'))
        
        # Validate required environment variables
        if not all([subnet_ids[0], security_group_id, iam_instance_profile]):
            raise ValueError("Missing required environment variables")
        
        # Generate user data script for the spot instance
        user_data_script = generate_user_data_script(timeout_minutes)
        
        # Prepare spot instance request
        spot_config = {
            'ImageId': os.environ.get('AMI_ID'),
            'InstanceType': instance_type,
            'SecurityGroupIds': [security_group_id],
            'SubnetId': subnet_ids[0],  # Use first available subnet
            'IamInstanceProfile': {'Name': iam_instance_profile},
            'UserData': user_data_script,
            'InstanceInitiatedShutdownBehavior': 'terminate',
            'TagSpecifications': [
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'parliament-import-{datetime.now().strftime("%Y%m%d-%H%M%S")}'},
                        {'Key': 'Purpose', 'Value': 'parliament-data-import'},
                        {'Key': 'ManagedBy', 'Value': 'terraform-lambda'},
                        {'Key': 'Environment', 'Value': os.environ.get('ENVIRONMENT', 'prod')},
                        {'Key': 'Project', 'Value': 'Parliament'},
                        {'Key': 'CostCenter', 'Value': 'Parliament-Analytics'},
                        {'Key': 'AutoTerminate', 'Value': 'true'}
                    ]
                }
            ]
        }
        
        # Add max price if specified
        spot_request = {
            'SpotPrice': max_price if max_price else None,
            'Type': 'one-time',
            'LaunchSpecification': spot_config
        }
        
        # Remove None values
        if not spot_request['SpotPrice']:
            del spot_request['SpotPrice']
        
        logger.info(f"Launching spot instance: {instance_type} in subnet {subnet_ids[0]}")
        
        # Request spot instance
        response = ec2_client.request_spot_instances(**spot_request)
        
        spot_request_id = response['SpotInstanceRequests'][0]['SpotInstanceRequestId']
        
        logger.info(f"Spot instance request created: {spot_request_id}")
        
        # Return success response
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': True,
                'message': 'Parliament data import job started successfully',
                'spot_request_id': spot_request_id,
                'instance_type': instance_type,
                'estimated_cost': f'$${calculate_estimated_cost(instance_type, timeout_minutes):.4f}',
                'timeout_minutes': timeout_minutes,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Failed to launch spot instance: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def generate_user_data_script(timeout_minutes: int) -> str:
    """Generate the user data script for the spot instance."""
    
    # Get environment variables for the script
    db_secret_arn = os.environ.get('DATABASE_SECRET_ARN', '')
    repo_url = os.environ.get('IMPORT_REPOSITORY', 'https://github.com/your-username/parliament.git')
    repo_branch = os.environ.get('IMPORT_BRANCH', 'main')
    script_path = os.environ.get('IMPORT_SCRIPT_PATH', 'scripts/data_processing/pipeline_orchestrator.py')
    python_packages = os.environ.get('PYTHON_REQUIREMENTS', 'requests sqlalchemy psycopg2-binary rich')
    log_group = os.environ.get('CLOUDWATCH_LOG_GROUP', '/aws/parliament/import')
    
    return f"""#!/bin/bash
exec > >(tee -a /var/log/user-data.log) 2>&1
echo "=== Parliament Data Import Job Started at $(date) ==="

# Install required packages
dnf update -y
dnf install -y python3 python3-pip git awscli

# Install Python dependencies
pip3 install {python_packages} boto3

# Configure AWS CLI for CloudWatch logs
aws configure set region {os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')}

# Create log group if it doesn't exist
aws logs create-log-group --log-group-name {log_group} 2>/dev/null || true

# Set up log stream
LOG_STREAM="import-$(date +%Y%m%d-%H%M%S)"
aws logs create-log-stream --log-group-name {log_group} --log-stream-name $LOG_STREAM

# Function to send logs to CloudWatch
send_log() {{
    echo "$1" | tee -a /tmp/import.log
    aws logs put-log-events --log-group-name {log_group} --log-stream-name $LOG_STREAM --log-events timestamp=$(date +%s000),message="$1" 2>/dev/null || true
}}

# Set timeout handler
timeout {timeout_minutes}m bash -c '
    send_log "Starting parliament data import..."
    
    # Clone repository
    cd /tmp
    if git clone -b {repo_branch} {repo_url} parliament; then
        send_log "Repository cloned successfully"
    else
        send_log "ERROR: Failed to clone repository"
        exit 1
    fi
    
    # Set up environment
    cd parliament
    export DATABASE_SECRET_ARN="{db_secret_arn}"
    export AWS_DEFAULT_REGION="{os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')}"
    export PYTHONPATH="/tmp/parliament:$PYTHONPATH"
    
    # Run import script
    send_log "Starting import script execution..."
    if python3 {script_path}; then
        send_log "Import script completed successfully"
        exit 0
    else
        send_log "ERROR: Import script failed"
        exit 1
    fi
' 

IMPORT_EXIT_CODE=$?

if [ $IMPORT_EXIT_CODE -eq 0 ]; then
    send_log "=== Parliament Data Import Job Completed Successfully at $(date) ==="
elif [ $IMPORT_EXIT_CODE -eq 124 ]; then
    send_log "=== Parliament Data Import Job Timed Out at $(date) ==="
else
    send_log "=== Parliament Data Import Job Failed at $(date) ==="
fi

# Upload final log to CloudWatch
if [ -f /tmp/import.log ]; then
    aws logs put-log-events --log-group-name {log_group} --log-stream-name $LOG_STREAM --log-events "$(jq -R -s 'split("\\n")[:-1] | map({{timestamp: (now * 1000 | floor), message: .}})' /tmp/import.log)" 2>/dev/null || true
fi

# Auto-terminate instance
send_log "Auto-terminating instance..."
shutdown -h now
"""

def calculate_estimated_cost(instance_type: str, duration_minutes: int) -> float:
    """Calculate estimated cost for spot instance execution."""
    
    # Approximate spot prices (actual prices vary)
    spot_prices = {
        't3.nano': 0.0017,
        't3.micro': 0.0034,
        't3.small': 0.0068,
        't4g.nano': 0.0017,
        't4g.micro': 0.0034,
        't4g.small': 0.0068
    }
    
    hourly_rate = spot_prices.get(instance_type, 0.0034)
    duration_hours = duration_minutes / 60.0
    
    return hourly_rate * duration_hours

EOF
    filename = "lambda_function.py"
  }
}

# Lambda function for spot instance launcher
resource "aws_lambda_function" "spot_launcher" {
  function_name = "${local.name_prefix}-spot-launcher"
  role          = aws_iam_role.spot_launcher.arn

  filename         = data.archive_file.spot_launcher.output_path
  source_code_hash = data.archive_file.spot_launcher.output_base64sha256
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.9"
  timeout          = 60  # 1 minute timeout
  memory_size      = 256 # Enough for EC2 API calls

  environment {
    variables = {
      SPOT_INSTANCE_TYPE     = var.spot_instance_type
      SPOT_MAX_PRICE         = ""  # Use current spot price
      IMPORT_TIMEOUT_MINUTES = var.import_timeout_minutes
      PRIVATE_SUBNET_IDS     = join(",", aws_subnet.private[*].id)
      SECURITY_GROUP_ID      = aws_security_group.spot_import.id
      IAM_INSTANCE_PROFILE   = aws_iam_instance_profile.spot_import.name
      AMI_ID                 = data.aws_ami.amazon_linux.id
      DATABASE_SECRET_ARN    = aws_secretsmanager_secret.db_credentials.arn
      IMPORT_REPOSITORY      = "https://github.com/your-username/parliament.git"
      IMPORT_BRANCH          = "main"
      IMPORT_SCRIPT_PATH     = "scripts/data_processing/pipeline_orchestrator.py"
      PYTHON_REQUIREMENTS    = "requests sqlalchemy psycopg2-binary rich boto3"
      CLOUDWATCH_LOG_GROUP   = aws_cloudwatch_log_group.spot_import.name
      ENVIRONMENT            = var.environment
      AWS_DEFAULT_REGION     = var.aws_region
    }
  }

  tags = merge(local.compute_tags, {
    Name         = "${local.name_prefix}-spot-launcher"
    ResourceType = "lambda-function"
    Purpose      = "spot-instance-launcher"
    Runtime      = "python3.9"
    MemorySize   = "256MB"
    Timeout      = "60s"
    FunctionType = "spot-launcher"
  })
}

# Lambda Function URL for manual triggers
resource "aws_lambda_function_url" "spot_launcher" {
  count = var.enable_automated_import ? 1 : 0

  function_name      = aws_lambda_function.spot_launcher.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["POST", "GET"]
    allow_headers     = ["date", "keep-alive", "content-type"]
    expose_headers    = ["date", "keep-alive"]
    max_age           = 86400
  }
}

# ============================================================================
# IAM ROLES AND POLICIES
# ============================================================================

# IAM Role for Lambda spot launcher
resource "aws_iam_role" "spot_launcher" {
  name = "${local.name_prefix}-spot-launcher-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.security_tags, {
    Name         = "${local.name_prefix}-spot-launcher-role"
    ResourceType = "iam-role"
    Purpose      = "spot-launcher-permissions"
  })
}

# Lambda basic execution policy
resource "aws_iam_role_policy_attachment" "spot_launcher_basic" {
  role       = aws_iam_role.spot_launcher.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Policy for EC2 spot instance management
resource "aws_iam_role_policy" "spot_launcher_ec2" {
  name = "${local.name_prefix}-spot-launcher-ec2"
  role = aws_iam_role.spot_launcher.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:RequestSpotInstances",
          "ec2:DescribeSpotInstanceRequests",
          "ec2:DescribeInstances",
          "ec2:DescribeImages",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:CreateTags"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = aws_iam_role.spot_import.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.spot_import.arn}:*"
      }
    ]
  })
}

# IAM Role for spot instances
resource "aws_iam_role" "spot_import" {
  name = "${local.name_prefix}-spot-import-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(local.security_tags, {
    Name         = "${local.name_prefix}-spot-import-role"
    ResourceType = "iam-role"
    Purpose      = "spot-instance-import-permissions"
  })
}

# Instance profile for spot instances
resource "aws_iam_instance_profile" "spot_import" {
  name = "${local.name_prefix}-spot-import-profile"
  role = aws_iam_role.spot_import.name

  tags = merge(local.security_tags, {
    Name         = "${local.name_prefix}-spot-import-profile"
    ResourceType = "iam-instance-profile"
    Purpose      = "spot-instance-profile"
  })
}

# Policy for spot instances to access database and CloudWatch
resource "aws_iam_role_policy" "spot_import_permissions" {
  name = "${local.name_prefix}-spot-import-permissions"
  role = aws_iam_role.spot_import.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = aws_secretsmanager_secret.db_credentials.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.spot_import.arn}:*",
          "arn:aws:logs:${var.aws_region}:*:log-group:/aws/parliament/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances"
        ]
        Resource = aws_db_instance.parliament.arn
      }
    ]
  })
}

# ============================================================================
# SECURITY GROUP FOR SPOT INSTANCES
# ============================================================================

resource "aws_security_group" "spot_import" {
  name_prefix = "${local.name_prefix}-spot-import-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for parliament data import spot instances"

  # Outbound HTTPS for package installation and git clone
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound HTTP for package repositories
  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # PostgreSQL access to RDS
  egress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.rds.id]
  }

  tags = merge(local.security_tags, {
    Name         = "${local.name_prefix}-spot-import-sg"
    ResourceType = "security-group"
    Purpose      = "spot-instance-network-access"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Update RDS security group to allow spot instances
resource "aws_security_group_rule" "rds_from_spot" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.spot_import.id
  security_group_id        = aws_security_group.rds.id
}

# ============================================================================
# EVENTBRIDGE SCHEDULING
# ============================================================================

# EventBridge rule for scheduled execution
resource "aws_cloudwatch_event_rule" "spot_import_schedule" {
  count = var.import_automation_mode == "daily" || var.import_automation_mode == "custom" ? 1 : 0

  name                = "${local.name_prefix}-spot-import-schedule"
  description         = "Scheduled parliament data import using spot instances"
  schedule_expression = var.import_automation_mode == "daily" ? "cron(0 2 * * ? *)" : var.import_schedule
  state              = "ENABLED"

  tags = merge(local.monitoring_tags, {
    Name         = "${local.name_prefix}-spot-import-schedule"
    ResourceType = "eventbridge-rule"
    Purpose      = "automated-import-scheduling"
    Schedule     = var.import_automation_mode == "daily" ? "daily-2am-utc" : "custom"
  })
}

# EventBridge target for Lambda function
resource "aws_cloudwatch_event_target" "spot_import_lambda" {
  count = var.import_automation_mode == "daily" || var.import_automation_mode == "custom" ? 1 : 0

  rule      = aws_cloudwatch_event_rule.spot_import_schedule[0].name
  target_id = "SpotImportLambdaTarget"
  arn       = aws_lambda_function.spot_launcher.arn

  input = jsonencode({
    source      = "eventbridge-schedule"
    mode        = var.import_automation_mode
    retry_count = 0
  })
}

# Lambda permission for EventBridge
resource "aws_lambda_permission" "allow_eventbridge" {
  count = var.import_automation_mode == "daily" || var.import_automation_mode == "custom" ? 1 : 0

  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.spot_launcher.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.spot_import_schedule[0].arn
}

# ============================================================================
# CLOUDWATCH MONITORING
# ============================================================================

# CloudWatch Log Group for import jobs
resource "aws_cloudwatch_log_group" "spot_import" {
  name              = "/aws/parliament/import"
  retention_in_days = 7

  tags = merge(local.monitoring_tags, {
    Name         = "${local.name_prefix}-spot-import-logs"
    ResourceType = "cloudwatch-log-group"
    Purpose      = "spot-import-application-logs"
    LogType      = "application"
    RetentionDays = tostring(var.import_log_retention_days)
  })
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "spot_launcher_logs" {
  name              = "/aws/lambda/${aws_lambda_function.spot_launcher.function_name}"
  retention_in_days = 7

  tags = merge(local.monitoring_tags, {
    Name         = "${local.name_prefix}-spot-launcher-logs"
    ResourceType = "cloudwatch-log-group"
    Purpose      = "lambda-application-logs"
    LogType      = "lambda"
    RetentionDays = tostring(var.import_log_retention_days)
  })
}

# CloudWatch alarm for import failures
resource "aws_cloudwatch_metric_alarm" "import_failures" {
  count = var.enable_automated_import && var.enable_basic_monitoring ? 1 : 0

  alarm_name          = "${local.name_prefix}-import-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Parliament data import job is failing"

  dimensions = {
    FunctionName = aws_lambda_function.spot_launcher.function_name
  }

  alarm_actions = var.import_alert_email != "" ? [aws_sns_topic.import_alerts[0].arn] : []

  tags = merge(local.monitoring_tags, {
    Name         = "${local.name_prefix}-import-failures"
    ResourceType = "cloudwatch-alarm"
    Purpose      = "import-failure-monitoring"
    AlarmType    = "import-failures"
  })
}

# SNS topic for import alerts
resource "aws_sns_topic" "import_alerts" {
  count = var.enable_automated_import && var.enable_basic_monitoring && var.import_alert_email != "" ? 1 : 0

  name = "${local.name_prefix}-import-alerts"

  tags = merge(local.monitoring_tags, {
    Name         = "${local.name_prefix}-import-alerts"
    ResourceType = "sns-topic"
    Purpose      = "import-alert-notifications"
  })
}

# SNS topic subscription
resource "aws_sns_topic_subscription" "import_alerts_email" {
  count = var.enable_automated_import && var.enable_basic_monitoring && var.import_alert_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.import_alerts[0].arn
  protocol  = "email"
  endpoint  = var.import_alert_email
}