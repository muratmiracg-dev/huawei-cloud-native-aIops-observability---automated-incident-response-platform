terraform {
  required_version = ">= 1.8.0"

  required_providers {
    huaweicloud = {
      source  = "huaweicloud/huaweicloud"
      version = "~> 1.95.0"
    }
  }
}
