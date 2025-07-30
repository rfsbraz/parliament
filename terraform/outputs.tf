# Terraform Outputs for Portuguese Parliament Infrastructure

# Common outputs
output "environment" {
  description = "Current environment"
  value       = var.environment
}

output "deployment_type" {
  description = "Current deployment type"
  value       = var.deployment_type
}

output "aws_region" {
  description = "AWS region"
  value       = var.aws_region
}

# Frontend outputs
output "s3_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = aws_s3_bucket.frontend.bucket
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = var.deployment_type == "serverless" ? aws_cloudfront_distribution.frontend_serverless[0].id : aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "CloudFront domain name"
  value       = var.deployment_type == "serverless" ? aws_cloudfront_distribution.frontend_serverless[0].domain_name : aws_cloudfront_distribution.frontend.domain_name
}

output "website_url" {
  description = "URL of the website"
  value       = var.domain_name != "" ? "https://${var.domain_name}" : "https://${var.deployment_type == "serverless" ? aws_cloudfront_distribution.frontend_serverless[0].domain_name : aws_cloudfront_distribution.frontend.domain_name}"
}

# Serverless outputs (Lambda + Aurora)
output "lambda_function_name" {
  description = "Lambda function name"
  value       = var.deployment_type == "serverless" ? aws_lambda_function.backend[0].function_name : null
}

output "lambda_function_url" {
  description = "Lambda function URL"
  value       = var.deployment_type == "serverless" ? aws_lambda_function_url.backend[0].function_url : null
}

output "aurora_cluster_identifier" {
  description = "Aurora cluster identifier"
  value       = var.deployment_type == "serverless" ? aws_rds_cluster.parliament[0].cluster_identifier : null
}

output "aurora_cluster_endpoint" {
  description = "Aurora cluster endpoint"
  value       = var.deployment_type == "serverless" ? aws_rds_cluster.parliament[0].endpoint : null
}

output "aurora_database_name" {
  description = "Aurora database name"
  value       = var.deployment_type == "serverless" ? aws_rds_cluster.parliament[0].database_name : null
}

output "aurora_master_user_secret_arn" {
  description = "Aurora master user secret ARN"
  value       = var.deployment_type == "serverless" ? aws_rds_cluster.parliament[0].master_user_secret[0].secret_arn : null
  sensitive   = true
}

# Fargate outputs (ECS)
output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = var.deployment_type == "fargate" ? aws_lb.backend[0].dns_name : null
}

output "alb_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = var.deployment_type == "fargate" ? aws_lb.backend[0].zone_id : null
}

output "backend_api_url" {
  description = "URL of the backend API"
  value       = var.deployment_type == "fargate" ? "http://${aws_lb.backend[0].dns_name}" : null
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = var.deployment_type == "fargate" ? aws_ecs_cluster.backend[0].name : null
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = var.deployment_type == "fargate" ? aws_ecs_service.backend[0].name : null
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = var.deployment_type == "serverless" ? aws_cloudwatch_log_group.lambda_backend[0].name : (var.deployment_type == "fargate" ? aws_cloudwatch_log_group.backend[0].name : null)
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.backend.repository_url
}

# Network outputs
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

# Cost optimization information
output "estimated_monthly_cost_usd" {
  description = "Estimated monthly cost in USD"
  value = var.deployment_type == "serverless" ? (
    var.environment == "prod" ? "15-25 (Aurora: $7-12, Lambda: $2-8, CloudFront: $1-3, other: $2-5)" :
    "5-10 (Aurora: $2-4, Lambda: $0-2, CloudFront: $1, other: $1-3)"
  ) : (
    var.environment == "prod" ? "150-200 (Fargate: $140-170, ALB: $18, other: $5-15)" :
    "80-120 (Fargate: $70-100, ALB: $18, other: $5-10)"
  )
}

# Environment-specific deployment instructions
output "deployment_instructions" {
  description = "Environment-specific deployment instructions"
  value = var.deployment_type == "serverless" ? <<EOF

=== SERVERLESS DEPLOYMENT INSTRUCTIONS (${upper(var.environment)}) ===

1. DATABASE MIGRATION:
   python3 scripts/migrate-to-aurora.py --environment ${var.environment} --action migrate

2. FRONTEND DEPLOYMENT:
   npm run build
   aws s3 sync build/ s3://${aws_s3_bucket.frontend.bucket}
   aws cloudfront create-invalidation --distribution-id ${var.deployment_type == "serverless" ? aws_cloudfront_distribution.frontend_serverless[0].id : aws_cloudfront_distribution.frontend.id} --paths "/*"

3. LAMBDA DEPLOYMENT:
   ./scripts/deploy-lambda-aurora.sh

4. ENDPOINTS:
   Website: ${var.domain_name != "" ? "https://${var.domain_name}" : "https://${var.deployment_type == "serverless" ? aws_cloudfront_distribution.frontend_serverless[0].domain_name : aws_cloudfront_distribution.frontend.domain_name}"}
   Lambda API: ${var.deployment_type == "serverless" ? aws_lambda_function_url.backend[0].function_url : "N/A"}
   Aurora: ${var.deployment_type == "serverless" ? aws_rds_cluster.parliament[0].endpoint : "N/A"}

5. MONITORING:
   aws logs tail /aws/lambda/${local.name_prefix}-backend --follow

6. TESTING:
   ./scripts/database-testing-toolkit.sh create-test-env test-${var.environment}

EOF
 : <<EOF

=== FARGATE DEPLOYMENT INSTRUCTIONS (${upper(var.environment)}) ===

1. DOCKER BUILD & PUSH:
   docker build -t parliament-backend .
   docker tag parliament-backend:latest ${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com/${aws_ecr_repository.backend.name}:latest
   aws ecr get-login-password --region ${data.aws_region.current.name} | docker login --username AWS --password-stdin ${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com
   docker push ${data.aws_caller_identity.current.account_id}.dkr.ecr.${data.aws_region.current.name}.amazonaws.com/${aws_ecr_repository.backend.name}:latest

2. ECS SERVICE UPDATE:
   aws ecs update-service --cluster ${var.deployment_type == "fargate" ? aws_ecs_cluster.backend[0].name : "N/A"} --service ${var.deployment_type == "fargate" ? aws_ecs_service.backend[0].name : "N/A"} --force-new-deployment

3. FRONTEND DEPLOYMENT:
   npm run build
   aws s3 sync build/ s3://${aws_s3_bucket.frontend.bucket}
   aws cloudfront create-invalidation --distribution-id ${aws_cloudfront_distribution.frontend.id} --paths "/*"

4. ENDPOINTS:
   Website: ${var.domain_name != "" ? "https://${var.domain_name}" : "https://${aws_cloudfront_distribution.frontend.domain_name}"}
   Backend API: ${var.deployment_type == "fargate" ? "http://${aws_lb.backend[0].dns_name}" : "N/A"}

5. MONITORING:
   aws logs tail /ecs/${local.name_prefix}-backend --follow

EOF
}