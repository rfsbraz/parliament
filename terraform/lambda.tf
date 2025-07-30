# Lambda function using AWS Lambda Web Adapter for zero-code-change migration
resource "aws_lambda_function" "backend" {

  function_name = "${local.name_prefix}-backend"
  role         = aws_iam_role.lambda_execution[0].arn
  
  # Use container image instead of ZIP
  package_type = "Image"
  image_uri    = var.backend_image
  
  # Memory and timeout configuration
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout
  
  # Environment variables
  environment {
    variables = {
      FLASK_ENV   = var.environment
      FLASK_DEBUG = var.environment == "dev" ? "1" : "0"
      # AWS Lambda Web Adapter configuration
      AWS_LWA_INVOKE_MODE = "response_stream"
      AWS_LWA_PORT       = "8000"
      # Database configuration
      DATABASE_TYPE = "mysql"
      DATABASE_HOST_SECRET_ARN = aws_rds_cluster.parliament.master_user_secret[0].secret_arn
      DATABASE_NAME = "parliament"
    }
  }

  # VPC configuration (required for Aurora access)
  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-backend-lambda"
  })
}

# Lambda Function URL for direct HTTP access
resource "aws_lambda_function_url" "backend" {

  function_name      = aws_lambda_function.backend.function_name
  authorization_type = "NONE"

  cors {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["*"]
    allow_headers     = ["date", "keep-alive"]
    expose_headers    = ["date", "keep-alive"]
    max_age          = 86400
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-backend-lambda-url"
  })
}

# IAM Role for Lambda Execution
resource "aws_iam_role" "lambda_execution" {

  name = "${local.name_prefix}-lambda-execution"

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

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-execution-role"
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Attach VPC execution policy
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_backend" {
  name              = "/aws/lambda/${local.name_prefix}-backend"
  retention_in_days = var.environment == "prod" ? 14 : 3  # Environment-specific retention

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-backend-logs"
  })
}

# Security Group for Lambda
resource "aws_security_group" "lambda" {
  name_prefix = "${local.name_prefix}-lambda-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for Lambda function"

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.tags, {
    Name = "${local.name_prefix}-lambda-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# CloudFront distribution using Lambda Function URL
resource "aws_cloudfront_distribution" "frontend" {

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
    origin_id                = "S3-${aws_s3_bucket.frontend.id}"
  }

  # Additional origin for Lambda backend API
  origin {
    domain_name = replace(replace(aws_lambda_function_url.backend.function_url, "https://", ""), "/", "")
    origin_id   = "Lambda-Backend"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
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

  # Cache behavior for API calls (forward to Lambda)
  ordered_cache_behavior {
    path_pattern           = "/api/*"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = "Lambda-Backend"
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

  price_class = "PriceClass_100"

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