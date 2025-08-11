# Cloudflare configuration for fiscaliza.pt
# This configures Cloudflare as the DNS provider and CDN for the domain

terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

# Cloudflare zone data (domain should already exist in Cloudflare)
data "cloudflare_zone" "fiscaliza" {
  count = var.domain_name == "fiscaliza.pt" ? 1 : 0
  name  = "fiscaliza.pt"
}

# DNS Records for fiscaliza.pt
# Main domain pointing to CloudFront
resource "cloudflare_record" "root" {
  count   = var.domain_name == "fiscaliza.pt" ? 1 : 0
  zone_id = data.cloudflare_zone.fiscaliza[0].id
  name    = "@"
  value   = aws_cloudfront_distribution.frontend.domain_name
  type    = "CNAME"
  proxied = true # Enable Cloudflare proxy for additional features

  comment = "Main fiscaliza.pt domain pointing to AWS CloudFront"

  depends_on = [aws_cloudfront_distribution.frontend]
}

# WWW subdomain
resource "cloudflare_record" "www" {
  count   = var.domain_name == "fiscaliza.pt" ? 1 : 0
  zone_id = data.cloudflare_zone.fiscaliza[0].id
  name    = "www"
  value   = "fiscaliza.pt"
  type    = "CNAME"
  proxied = true

  comment = "WWW redirect to main domain"
}

# API subdomain (optional - for future API separation)
resource "cloudflare_record" "api" {
  count   = var.domain_name == "fiscaliza.pt" && var.create_api_subdomain ? 1 : 0
  zone_id = data.cloudflare_zone.fiscaliza[0].id
  name    = "api"
  value   = aws_cloudfront_distribution.frontend.domain_name
  type    = "CNAME"
  proxied = true

  comment = "API subdomain for future API endpoints"
}

# Cloudflare page rules for performance and security
resource "cloudflare_page_rule" "root_redirect" {
  count   = var.domain_name == "fiscaliza.pt" ? 1 : 0
  zone_id = data.cloudflare_zone.fiscaliza[0].id
  target  = "www.fiscaliza.pt/*"
  
  actions {
    forwarding_url {
      url         = "https://fiscaliza.pt/$1"
      status_code = 301
    }
  }

  priority = 1
}

# Security settings for fiscaliza.pt
resource "cloudflare_zone_settings_override" "fiscaliza_settings" {
  count   = var.domain_name == "fiscaliza.pt" ? 1 : 0
  zone_id = data.cloudflare_zone.fiscaliza[0].id

  settings {
    # Security settings
    ssl                      = "flexible"  # Let Cloudflare handle SSL termination
    always_use_https         = "on"
    automatic_https_rewrites = "on"
    security_level           = "medium"
    challenge_ttl           = 1800

    # Performance settings
    browser_cache_ttl = 14400  # 4 hours
    browser_check     = "on"
    cache_level       = "aggressive"
    
    # Compression and optimization
    brotli              = "on"
    minify {
      css  = "on"
      html = "on"
      js   = "on"
    }
    
    # Modern web features
    http3               = "on"
    zero_rtt            = "on"
    tls_1_3             = "zrt"
    
    # Bot protection
    bot_fight_mode = "on"
  }
}

# WAF rules for additional security (Cloudflare's Web Application Firewall)
resource "cloudflare_ruleset" "fiscaliza_waf" {
  count   = var.domain_name == "fiscaliza.pt" && var.enable_cloudflare_waf ? 1 : 0
  zone_id = data.cloudflare_zone.fiscaliza[0].id
  name    = "Fiscaliza WAF Rules"
  kind    = "zone"
  phase   = "http_request_firewall_custom"

  rules {
    action = "challenge"
    expression = "(http.request.uri.path contains \"/api/\" and cf.threat_score gt 10)"
    description = "Challenge suspicious requests to API endpoints"
    enabled = true
  }

  rules {
    action = "block"
    expression = "(http.request.method eq \"POST\" and cf.threat_score gt 25)"
    description = "Block high-risk POST requests"
    enabled = true
  }
}

# Rate limiting for API protection
resource "cloudflare_rate_limit" "api_rate_limit" {
  count   = var.domain_name == "fiscaliza.pt" ? 1 : 0
  zone_id = data.cloudflare_zone.fiscaliza[0].id

  threshold = 100  # requests
  period    = 60   # seconds
  
  match {
    request {
      url_pattern = "fiscaliza.pt/api/*"
      schemes     = ["HTTPS"]
      methods     = ["GET", "POST"]
    }
  }

  action {
    mode    = "challenge"
    timeout = 300  # 5 minutes
  }

  disabled    = false
  description = "Rate limiting for API endpoints"
}