# Portuguese Parliament - AWS Deployment

This document describes how to deploy the Portuguese Parliament application to AWS using a fully managed, serverless architecture.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │────│       S3        │    │   Users/Web     │
│   (CDN/Cache)   │    │ (Static Files)  │    │   Browsers      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         │ /api/* requests
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      ALB        │────│   ECS Fargate   │────│     SQLite      │
│ (Load Balancer) │    │   (Backend)     │    │   (Embedded)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Components

- **Frontend**: React SPA → S3 → CloudFront
- **Backend**: Flask API + SQLite DB → Docker → ECS Fargate → Application Load Balancer
- **Infrastructure**: Fully managed by Terraform

## Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **Docker** for building images
3. **Terraform** >= 1.0
4. **Node.js** >= 18 for frontend builds
5. **Git** for version control

## Quick Start

### 1. Clone and Prepare

```bash
git clone <repository>
cd parliament
```

### 2. Configure Terraform

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your configuration
```

### 3. Deploy Everything

```bash
# Make the deployment script executable
chmod +x scripts/deploy/deploy.sh

# Run the deployment
./scripts/deploy/deploy.sh
```

The script will:
1. ✅ Deploy AWS infrastructure (VPC, ECS, ALB, S3, CloudFront)
2. ✅ Build and push Docker image to ECR
3. ✅ Build and deploy React frontend to S3
4. ✅ Update ECS service with new image
5. ✅ Invalidate CloudFront cache

## Manual Deployment Steps

### Infrastructure

```bash
cd terraform
terraform init
terraform plan -var="aws_region=eu-west-1"
terraform apply -var="aws_region=eu-west-1"
```

### Backend

```bash
# Get ECR repository URL
ECR_REPO=$(terraform output -raw ecr_repository_url)

# Login to ECR
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin $ECR_REPO

# Build and push
docker build -t parliament-backend .
docker tag parliament-backend:latest $ECR_REPO:latest
docker push $ECR_REPO:latest

# Update ECS service
aws ecs update-service --cluster parliament-prod-cluster --service parliament-prod-backend-service --force-new-deployment
```

### Frontend

```bash
cd frontend
npm ci
npm run build

# Upload to S3
S3_BUCKET=$(cd ../terraform && terraform output -raw s3_bucket_name)
aws s3 sync build/ s3://$S3_BUCKET --delete

# Invalidate CloudFront
DISTRIBUTION_ID=$(cd ../terraform && terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"
```

## Configuration Options

### terraform.tfvars

```hcl
# Basic configuration
aws_region = "eu-west-1"
environment = "prod"

# Custom domain (optional)
domain_name = "parliament.yourdomain.com"
certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/..."

# Backend scaling
backend_cpu = 512
backend_memory = 1024
backend_desired_count = 2

# Database persistence (adds EFS - optional)
enable_database_persistence = false
```

### Environment Variables

The backend container receives these environment variables:

- `FLASK_ENV`: production
- `FLASK_DEBUG`: 0 (production)
- `PYTHONPATH`: /app

## Database Considerations

### Embedded SQLite (Default)

- ✅ **Pros**: Simple, no additional cost, fast reads
- ❌ **Cons**: Data lost on container restart, single writer

The SQLite database is embedded in the Docker image, making it perfect for read-heavy applications like this parliamentary data viewer.

### EFS Persistence (Optional)

Set `enable_database_persistence = true` to mount an EFS volume:

- ✅ **Pros**: Data persists across deployments
- ❌ **Cons**: Additional cost (~$0.30/GB/month), slightly slower

## Monitoring & Operations

### Health Checks

The application includes health check endpoints:

- `/api/health` - Basic health check
- `/api/ready` - Readiness check (database connectivity)

### Logs

View application logs:

```bash
# Get log group name
LOG_GROUP=$(cd terraform && terraform output -raw log_group_name)

# View logs
aws logs tail $LOG_GROUP --follow
```

### Scaling

Adjust scaling in `terraform.tfvars`:

```hcl
backend_desired_count = 4  # Scale to 4 instances
backend_cpu = 1024        # More CPU
backend_memory = 2048     # More memory
```

Then apply:

```bash
cd terraform
terraform apply
```

## Cost Estimation

### Monthly costs (eu-west-1):

| Service | Usage | Cost |
|---------|-------|------|
| ECS Fargate | 2 tasks, 0.5 vCPU, 1GB RAM | ~$25 |
| Application Load Balancer | Always on | ~$20 |
| CloudFront | 1TB transfer | ~$85 |
| S3 | 1GB storage, requests | ~$1 |
| NAT Gateway | 2 AZs | ~$45 |
| **Total** | | **~$176/month** |

### Cost Optimization

1. **Single AZ**: Deploy to one AZ only (-$22/month)
2. **Fargate Spot**: Use spot instances (-30% on compute)
3. **CloudFront optimization**: Reduce price class (-50% on CDN)

## Security Features

- ✅ VPC with private subnets for backend
- ✅ Security groups with minimal required access
- ✅ ALB with health checks
- ✅ Container runs as non-root user
- ✅ S3 bucket with public access blocked
- ✅ CloudFront with HTTPS redirect
- ✅ IAM roles with least privilege

## Troubleshooting

### Backend won't start

```bash
# Check ECS service status
aws ecs describe-services --cluster parliament-prod-cluster --services parliament-prod-backend-service

# Check task logs
aws logs tail /ecs/parliament-prod-backend --follow
```

### Frontend not loading

```bash
# Check S3 bucket contents
aws s3 ls s3://$(cd terraform && terraform output -raw s3_bucket_name)

# Check CloudFront distribution
aws cloudfront get-distribution --id $(cd terraform && terraform output -raw cloudfront_distribution_id)
```

### Database issues

```bash
# Check health endpoint
curl https://your-alb-dns-name/api/health

# Check readiness endpoint
curl https://your-alb-dns-name/api/ready
```

## Cleanup

To destroy all AWS resources:

```bash
cd terraform
terraform destroy
```

⚠️ **Warning**: This will permanently delete all data and resources!

## Support

For issues with:
- **Infrastructure**: Check Terraform plan/apply output
- **Backend**: Check ECS task logs in CloudWatch
- **Frontend**: Check S3 bucket contents and CloudFront distribution
- **Database**: Check health endpoints and task logs

---

🏛️ **Portuguese Parliament Application** - Powered by AWS, managed by Terraform