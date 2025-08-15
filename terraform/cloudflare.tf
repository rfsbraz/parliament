# Cloudflare Configuration for fiscaliza.pt
# Provides CDN, caching, security, and routing to Lambda Function URL
# Replaces expensive AWS services with Cloudflare's free/pro tier

# Data source for the existing zone
data "cloudflare_zone" "fiscaliza" {
  count = var.cloudflare_zone_id != "" ? 1 : 0

  zone_id = var.cloudflare_zone_id
}

# Main A record pointing to Lambda Function URL
resource "cloudflare_record" "main" {
  count = var.cloudflare_zone_id != "" ? 1 : 0

  zone_id = var.cloudflare_zone_id
  name    = "@" # Root domain
  value   = replace(replace(aws_lambda_function_url.backend.function_url, "https://", ""), "/", "")
  type    = "CNAME"
  proxied = true # Enable Cloudflare proxy (CDN + security)

  comment = "Main application pointing to AWS Lambda Function URL"
}

# WWW CNAME record
resource "cloudflare_record" "www" {
  count = var.cloudflare_zone_id != "" ? 1 : 0

  zone_id = var.cloudflare_zone_id
  name    = "www"
  value   = var.domain_name
  type    = "CNAME"
  proxied = true

  comment = "WWW redirect to main domain"
}

# Page Rules for caching optimization
resource "cloudflare_page_rule" "api_bypass_cache" {
  count = var.cloudflare_zone_id != "" ? 1 : 0

  zone_id  = var.cloudflare_zone_id
  target   = "${var.domain_name}/api/*"
  priority = 1

  actions {
    cache_level = "bypass"

    # Security headers for API
    security_level = "medium"

    # Disable unnecessary features for API
    disable_apps        = true
    disable_performance = false
    disable_railgun     = true
    disable_zaraz       = true
  }
}

resource "cloudflare_page_rule" "static_cache_everything" {
  count = var.cloudflare_zone_id != "" && var.enable_cloudflare_cache ? 1 : 0

  zone_id  = var.cloudflare_zone_id
  target   = "${var.domain_name}/static/*"
  priority = 2

  actions {
    cache_level       = "cache_everything"
    edge_cache_ttl    = 86400 # 24 hours
    browser_cache_ttl = 3600  # 1 hour
  }
}

resource "cloudflare_page_rule" "assets_cache_everything" {
  count = var.cloudflare_zone_id != "" && var.enable_cloudflare_cache ? 1 : 0

  zone_id  = var.cloudflare_zone_id
  target   = "${var.domain_name}/*.{css,js,png,jpg,jpeg,gif,ico,svg,woff,woff2,ttf,eot}"
  priority = 3

  actions {
    cache_level       = "cache_everything"
    edge_cache_ttl    = 172800 # 48 hours
    browser_cache_ttl = 86400  # 24 hours
  }
}

resource "cloudflare_page_rule" "root_cache_level" {
  count = var.cloudflare_zone_id != "" ? 1 : 0

  zone_id  = var.cloudflare_zone_id
  target   = "${var.domain_name}/*"
  priority = 4

  actions {
    cache_level       = var.cloudflare_cache_level
    browser_cache_ttl = 300 # 5 minutes for dynamic content

    # Performance optimizations
    minify {
      css  = "on"
      html = "on"
      js   = "on"
    }

    # Security
    security_level = "medium"
    ssl            = "flexible" # Accept HTTP from origin, serve HTTPS to visitors
  }
}

# Zone settings optimization
resource "cloudflare_zone_settings_override" "fiscaliza" {
  count = var.cloudflare_zone_id != "" ? 1 : 0

  zone_id = var.cloudflare_zone_id

  settings {
    # SSL/TLS settings
    ssl                      = "flexible"
    always_use_https         = "on"
    min_tls_version          = "1.2"
    tls_1_3                  = "on"
    automatic_https_rewrites = "on"

    # Security settings
    security_level      = "medium"
    challenge_ttl       = 1800
    browser_check       = "on"
    hotlink_protection  = "on"
    email_obfuscation   = "on"
    server_side_exclude = "on"

    # Performance settings
    brotli = "on"
    minify {
      css  = "on"
      html = "on"
      js   = "on"
    }
    rocket_loader = "on"
    mirage        = "on"
    polish        = "lossless"

    # Caching settings
    browser_cache_ttl = 3600 # 1 hour
    always_online     = "on"
    development_mode  = var.environment == "dev" ? "on" : "off"

    # IP Geolocation
    ip_geolocation = "on"

    # HTTP/2 and HTTP/3
    http2 = "on"
    http3 = "on"

    # Zero Downtime Failover
    origin_error_page_pass_thru = "off"
  }
}

# Rate limiting rules for cost optimization and security
resource "cloudflare_rate_limit" "api_rate_limit" {
  count = var.cloudflare_zone_id != "" && var.enable_cloudflare_waf ? 1 : 0

  zone_id   = var.cloudflare_zone_id
  threshold = 100 # Max 100 requests
  period    = 60  # Per minute

  match {
    request {
      url_pattern = "${var.domain_name}/api/*"
      schemes     = ["HTTP", "HTTPS"]
      methods     = ["GET", "POST", "PUT", "DELETE"]
    }
  }

  action {
    mode    = "challenge" # Challenge instead of block
    timeout = 60
  }

  # Bypass rate limiting for specific paths
  bypass_url_patterns = [
    "${var.domain_name}/api/health",
    "${var.domain_name}/api/status"
  ]
}

resource "cloudflare_rate_limit" "global_rate_limit" {
  count = var.cloudflare_zone_id != "" && var.enable_cloudflare_waf ? 1 : 0

  zone_id   = var.cloudflare_zone_id
  threshold = 200 # Max 200 requests
  period    = 60  # Per minute

  match {
    request {
      url_pattern = "${var.domain_name}/*"
      schemes     = ["HTTP", "HTTPS"]
      methods     = ["_ALL_"]
    }
  }

  action {
    mode    = "challenge"
    timeout = 300 # 5 minutes
  }
}

# Firewall rules for additional protection
resource "cloudflare_filter" "block_bad_bots" {
  count = var.cloudflare_zone_id != "" && var.enable_cloudflare_waf ? 1 : 0

  zone_id     = var.cloudflare_zone_id
  description = "Block known bad bots and scrapers"
  expression  = "(cf.client.bot) or (http.user_agent contains \"scrapy\") or (http.user_agent contains \"crawler\")"
}

resource "cloudflare_firewall_rule" "block_bad_bots" {
  count = var.cloudflare_zone_id != "" && var.enable_cloudflare_waf ? 1 : 0

  zone_id     = var.cloudflare_zone_id
  description = "Block bad bots and scrapers"
  filter_id   = cloudflare_filter.block_bad_bots[0].id
  action      = "block"
  priority    = 1
}

resource "cloudflare_filter" "challenge_suspicious" {
  count = var.cloudflare_zone_id != "" && var.enable_cloudflare_waf ? 1 : 0

  zone_id     = var.cloudflare_zone_id
  description = "Challenge suspicious requests"
  expression  = "(cf.threat_score gt 10) or (not cf.verified_bot)"
}

resource "cloudflare_firewall_rule" "challenge_suspicious" {
  count = var.cloudflare_zone_id != "" && var.enable_cloudflare_waf ? 1 : 0

  zone_id     = var.cloudflare_zone_id
  description = "Challenge suspicious traffic"
  filter_id   = cloudflare_filter.challenge_suspicious[0].id
  action      = "challenge"
  priority    = 2
}