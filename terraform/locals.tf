locals {
  name = "${var.project_name}-${var.environment}"
  common_tags = {
    Project     = "Huawei Cloud-Native AIOps"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "Murat Mirac Gedik"
  }

  repositories = toset([
    "catalog-api",
    "orders-api",
    "payments-api",
    "aiops-api",
  ])
}
