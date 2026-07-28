resource "huaweicloud_vpc" "platform" {
  name = "${local.name}-vpc"
  cidr = var.vpc_cidr
  tags = local.common_tags
}

resource "huaweicloud_vpc_subnet" "cce" {
  name          = "${local.name}-cce-subnet"
  cidr          = var.subnet_cidr
  gateway_ip    = var.subnet_gateway
  vpc_id        = huaweicloud_vpc.platform.id
  primary_dns   = "100.125.1.250"
  secondary_dns = "100.125.21.250"
  tags          = local.common_tags
}
