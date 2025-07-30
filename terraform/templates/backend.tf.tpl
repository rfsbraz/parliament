# Terraform Backend Configuration
# Generated automatically by remote_state.tf

terraform {
  backend "s3" {
    bucket         = "${bucket}"
    key            = "${key}"
    region         = "${region}"
    dynamodb_table = "${dynamodb_table}"
    encrypt        = ${encrypt}
  }
}