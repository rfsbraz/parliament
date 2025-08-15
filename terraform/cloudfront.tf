# Cost-Optimized CloudFront Configuration
# Simplified to serve only S3 static assets, not the application
# Target cost: ~$1-2/month vs ~$5-10/month for full distribution

# S3 Bucket for static assets (JS, CSS, images)
resource "aws_s3_bucket" "static_assets" {
  count = var.enable_cloudfront ? 1 : 0

  bucket = "${local.name_prefix}-static-assets"

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-static-assets"
  })
}

# S3 Bucket versioning
resource "aws_s3_bucket_versioning" "static_assets" {
  count = var.enable_cloudfront ? 1 : 0

  bucket = aws_s3_bucket.static_assets[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "static_assets" {
  count = var.enable_cloudfront ? 1 : 0

  bucket = aws_s3_bucket.static_assets[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket public access block
resource "aws_s3_bucket_public_access_block" "static_assets" {
  count = var.enable_cloudfront ? 1 : 0

  bucket = aws_s3_bucket.static_assets[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudFront Origin Access Control
resource "aws_cloudfront_origin_access_control" "static_assets" {
  count = var.enable_cloudfront ? 1 : 0

  name                              = "${local.name_prefix}-static-assets-oac"
  description                       = "OAC for static assets S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Distribution for static assets only
resource "aws_cloudfront_distribution" "static_assets" {
  count = var.enable_cloudfront ? 1 : 0

  origin {
    domain_name              = aws_s3_bucket.static_assets[0].bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.static_assets[0].id
    origin_id                = "S3-${aws_s3_bucket.static_assets[0].id}"
  }

  enabled = true
  comment = "Static assets CDN for fiscaliza.pt"

  # No custom domain - use CloudFront domain
  # This saves on SSL certificate costs

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.static_assets[0].id}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]
      cookies {
        forward = "none"
      }
    }

    # Aggressive caching for static assets
    min_ttl     = 86400    # 1 day
    default_ttl = 604800   # 1 week
    max_ttl     = 31536000 # 1 year
  }

  # Cost optimization - only US, Canada, Europe
  price_class = var.cloudfront_price_class

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-static-assets-cloudfront"
  })
}

# S3 Bucket Policy for CloudFront access
resource "aws_s3_bucket_policy" "static_assets" {
  count = var.enable_cloudfront ? 1 : 0

  bucket = aws_s3_bucket.static_assets[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.static_assets[0].arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.static_assets[0].arn
          }
        }
      }
    ]
  })
}