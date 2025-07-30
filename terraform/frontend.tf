# S3 Bucket for Static Website
resource "aws_s3_bucket" "frontend" {
  bucket = "${local.name_prefix}-frontend-${random_string.bucket_suffix.result}"

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-frontend"
  })
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# CloudFront Origin Access Control
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${local.name_prefix}-frontend-oac"
  description                       = "OAC for ${local.name_prefix} frontend"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "frontend" {
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
    origin_id                = "S3-${aws_s3_bucket.frontend.id}"
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Portuguese Parliament Frontend"
  default_root_object = "index.html"

  # Aliases (if domain is provided)
  aliases = var.domain_name != "" ? [var.domain_name] : []

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.frontend.id}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  # Cache behavior for API calls (only for Fargate deployment)
  dynamic "ordered_cache_behavior" {
    for_each = var.deployment_type == "fargate" ? [1] : []
    content {
      path_pattern           = "/api/*"
      allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
      cached_methods         = ["GET", "HEAD", "OPTIONS"]
      target_origin_id       = "ALB-Backend"
      compress               = true
      viewer_protocol_policy = "redirect-to-https"

      forwarded_values {
        query_string = true
        headers      = ["*"]
        cookies {
          forward = "all"
        }
      }

      min_ttl     = 0
      default_ttl = 0
      max_ttl     = 0
    }
  }

  # Additional origin for backend API (only for Fargate deployment)
  dynamic "origin" {
    for_each = var.deployment_type == "fargate" ? [1] : []
    content {
      domain_name = aws_lb.backend[0].dns_name
      origin_id   = "ALB-Backend"

      custom_origin_config {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "http-only"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
  }

  price_class = "PriceClass_100"  # Use only North America and Europe

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    # Use custom SSL certificate if provided
    dynamic "viewer_certificate" {
      for_each = var.certificate_arn != "" ? [1] : []
      content {
        acm_certificate_arn      = var.certificate_arn
        ssl_support_method       = "sni-only"
        minimum_protocol_version = "TLSv1.2_2021"
      }
    }

    # Use default CloudFront certificate
    dynamic "viewer_certificate" {
      for_each = var.certificate_arn == "" ? [1] : []
      content {
        cloudfront_default_certificate = true
      }
    }
  }

  # Custom error pages for SPA
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-cloudfront"
  })
}

# S3 Bucket Policy to allow CloudFront access
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

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
        Resource = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })
}