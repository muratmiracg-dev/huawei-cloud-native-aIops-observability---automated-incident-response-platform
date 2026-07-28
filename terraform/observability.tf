resource "huaweicloud_obs_bucket" "observability" {
  bucket     = var.observability_bucket_name
  acl        = "private"
  versioning = true

  lifecycle_rule {
    name    = "archive-observability-data"
    enabled = true

    transition {
      days          = 30
      storage_class = "WARM"
    }

    expiration {
      days = 365
    }
  }

  tags = local.common_tags
}
