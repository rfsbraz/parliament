# Variables for Backend Setup
# These variables are used only for bootstrapping the remote state infrastructure

variable "aws_region" {
  description = "AWS region for backend infrastructure"
  type        = string
  default     = "eu-west-1"
}