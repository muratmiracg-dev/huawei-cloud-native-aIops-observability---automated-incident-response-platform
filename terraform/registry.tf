resource "huaweicloud_swr_organization" "platform" {
  name = var.swr_organization
}

resource "huaweicloud_swr_repository" "services" {
  for_each = local.repositories

  organization = huaweicloud_swr_organization.platform.name
  name         = each.value
  description  = "Private image repository for ${each.value}."
  category     = "app_server"
  is_public    = false
}
