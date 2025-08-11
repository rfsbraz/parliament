# Fiscaliza Deployment Guide

Complete deployment guide for Fiscaliza.pt - Portuguese Parliament Transparency Platform.

## 🌐 Production Environment

**Live URL**: https://fiscaliza.pt  
**Infrastructure**: AWS + Cloudflare  
**Deployment**: Serverless (Lambda + Aurora + CloudFront + S3)  

## 🏗️ Infrastructure Overview

### Architecture
- **Domain**: Managed by Cloudflare (fiscaliza.pt)
- **CDN**: Cloudflare (proxy) + AWS CloudFront (origin)
- **Frontend**: React SPA hosted on S3, served via CloudFront
- **Backend**: Python Flask on AWS Lambda
- **Database**: Aurora Serverless v2 (PostgreSQL-compatible)
- **Monitoring**: CloudWatch + Cloudflare Analytics

### Cost Optimization
- **Production**: ~€20-30/month
- **Staging**: ~€8-15/month  
- **Development**: ~€5-10/month

## 📋 Prerequisites

### Required Accounts
- [ ] AWS Account with appropriate IAM permissions
- [ ] Cloudflare account with fiscaliza.pt domain
- [ ] GitHub account for CI/CD (optional)

### Local Development Setup
```bash
# Install Terraform
brew install terraform  # macOS
# or
sudo apt-get install terraform  # Ubuntu

# Install AWS CLI
pip install awscli
aws configure

# Install Cloudflare CLI (optional)
npm install -g wrangler
```

### Required Environment Variables
```bash
# AWS
export AWS_REGION=eu-west-1
export AWS_PROFILE=default

# Cloudflare
export CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
export CLOUDFLARE_ZONE_ID=your-zone-id
```

## 🚀 Deployment Steps

### 1. Infrastructure Setup

#### Initialize Terraform
```bash
cd terraform
terraform init
```

#### Plan Infrastructure (Production)
```bash
terraform plan -var-file="environments/prod.tfvars"
```

#### Deploy Infrastructure
```bash
# Deploy to production
terraform apply -var-file="environments/prod.tfvars"

# Deploy to staging
terraform apply -var-file="environments/staging.tfvars"

# Deploy to development
terraform apply -var-file="environments/dev.tfvars"
```

### 2. Domain Configuration

#### Cloudflare Setup
1. Add fiscaliza.pt to Cloudflare
2. Update nameservers at domain registrar
3. Configure SSL/TLS mode to "Flexible" or "Full"
4. Enable security features:
   - Always Use HTTPS: On
   - HTTP Strict Transport Security (HSTS): Enable
   - Automatic HTTPS Rewrites: On

#### DNS Verification
```bash
# Verify DNS propagation
nslookup fiscaliza.pt
dig fiscaliza.pt
```

### 3. Database Migration

#### Prepare Database
```bash
# Run database migrations
python scripts/migrate-to-aurora.py --environment production --action migrate

# Verify database connection
python -c "from app.database.aurora_connection import get_connection; print('Connection OK' if get_connection() else 'Connection Failed')"
```

### 4. Frontend Deployment

#### Build and Deploy
```bash
cd frontend
npm install
npm run build

# Get S3 bucket name from Terraform output
BUCKET_NAME=$(terraform output -raw s3_bucket_name)

# Upload to S3
aws s3 sync dist/ s3://$BUCKET_NAME --delete

# Get CloudFront distribution ID
DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id)

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"
```

### 5. Backend Deployment

#### Lambda Deployment
```bash
# Deploy Lambda function
./scripts/deploy-lambda-aurora.sh

# Verify Lambda function
aws lambda invoke --function-name fiscaliza-prod-backend response.json
cat response.json
```

### 6. Verification & Testing

#### Health Check
```bash
# Test website
curl -I https://fiscaliza.pt

# Test API endpoints (if available)
curl https://fiscaliza.pt/api/health
```

#### Performance Testing
- **Lighthouse**: Run performance audit
- **WebPageTest**: Test from multiple locations
- **Cloudflare Analytics**: Monitor real-user metrics

## 🔧 Configuration Files

### Environment-Specific Configurations

#### Production (`terraform/environments/prod.tfvars`)
- Domain: fiscaliza.pt
- Aurora: 1-16 ACU capacity
- Lambda: 1024MB memory
- CloudFront: Global distribution
- WAF: Enabled
- Monitoring: Enhanced

#### Staging (`terraform/environments/staging.tfvars`)  
- No custom domain
- Aurora: 0.5-2 ACU capacity
- Lambda: 512MB memory
- CloudFront: Europe/US only
- WAF: Disabled
- Monitoring: Basic

#### Development (`terraform/environments/dev.tfvars`)
- No custom domain  
- Aurora: 0.5-1 ACU capacity
- Lambda: 512MB memory
- CloudFront: Europe only
- WAF: Disabled
- Monitoring: Basic

### Cloudflare Configuration

#### Security Settings
- Security Level: Medium
- Bot Fight Mode: On
- Browser Integrity Check: On
- Challenge Passage: 30 minutes

#### Performance Settings
- Caching Level: Aggressive
- Browser Cache TTL: 4 hours
- Always Online: On
- HTTP/2: Enabled
- HTTP/3 (QUIC): Enabled

#### Page Rules
1. `www.fiscaliza.pt/*` → Redirect to `fiscaliza.pt/$1` (301)
2. `fiscaliza.pt/api/*` → Cache Level: Bypass (for API calls)

## 🔍 Monitoring & Maintenance

### Health Monitoring
- **Uptime**: Cloudflare uptime monitoring
- **Performance**: Core Web Vitals via Cloudflare RUM
- **Errors**: CloudWatch alarms for Lambda errors
- **Database**: Aurora performance insights

### Log Locations
- **Lambda Logs**: CloudWatch `/aws/lambda/fiscaliza-{env}-backend`
- **CloudFront Logs**: S3 bucket (if enabled)
- **Aurora Logs**: CloudWatch `/aws/rds/cluster/fiscaliza-{env}/`

### Backup Strategy
- **Database**: Daily automated snapshots (30-day retention)
- **Frontend**: S3 versioning enabled
- **Infrastructure**: Terraform state in S3 with versioning

### Cost Monitoring
- Set up AWS Budget alerts
- Monitor Cloudflare usage
- Review monthly AWS cost reports

## 🚨 Troubleshooting

### Common Issues

#### Domain Not Resolving
1. Check Cloudflare DNS propagation
2. Verify nameserver configuration
3. Check Cloudflare proxy status (should be orange cloud)

#### SSL Errors
1. Verify Cloudflare SSL/TLS mode
2. Check certificate status in Cloudflare
3. Test with `curl -v https://fiscaliza.pt`

#### Lambda Errors
1. Check CloudWatch logs
2. Verify environment variables
3. Test Lambda function directly

#### Database Connection Issues
1. Check Aurora cluster status
2. Verify VPC security groups
3. Test connection from Lambda

### Performance Optimization

#### Frontend
- Enable Cloudflare minification (HTML, CSS, JS)
- Use Cloudflare image optimization
- Implement proper caching headers

#### Backend  
- Enable Lambda provisioned concurrency for production
- Optimize database queries
- Use Aurora query plan cache

#### Database
- Monitor Aurora performance insights
- Optimize query patterns
- Consider read replicas for heavy read workloads

## 📞 Support & Maintenance

### Regular Maintenance Tasks
- [ ] Weekly: Review CloudWatch metrics and alarms
- [ ] Monthly: Check AWS costs and optimize
- [ ] Quarterly: Update dependencies and security patches
- [ ] Annually: Review infrastructure architecture

### Emergency Contacts
- **AWS Support**: (if applicable)
- **Cloudflare Support**: Available via dashboard
- **Domain Registrar**: Contact details in registrar account

### Rollback Procedures
1. **Frontend**: Restore previous S3 version + CloudFront invalidation
2. **Backend**: Redeploy previous Lambda version
3. **Database**: Restore from Aurora snapshot (downtime required)
4. **Infrastructure**: `terraform apply` with previous configuration

---

**Last Updated**: $(date)  
**Version**: 1.0  
**Infrastructure**: Serverless (AWS + Cloudflare)