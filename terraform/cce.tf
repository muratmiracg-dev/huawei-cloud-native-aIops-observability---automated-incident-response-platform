resource "huaweicloud_cce_cluster" "platform" {
  name                   = "${local.name}-cce"
  cluster_type           = "VirtualMachine"
  cluster_version        = var.cluster_version
  flavor_id              = var.cluster_flavor
  vpc_id                 = huaweicloud_vpc.platform.id
  subnet_id              = huaweicloud_vpc_subnet.cce.id
  container_network_type = "overlay_l2"
  authentication_mode    = "rbac"
  description            = "CCE cluster for AIOps, observability, and SRE automation."

  tags = local.common_tags
}

resource "huaweicloud_cce_node_pool" "platform" {
  cluster_id               = huaweicloud_cce_cluster.platform.id
  name                     = "${local.name}-workers"
  os                       = var.node_os
  initial_node_count       = var.initial_node_count
  flavor_id                = var.node_flavor
  availability_zone        = var.availability_zone
  key_pair                 = var.key_pair_name
  scall_enable             = true
  min_node_count           = 2
  max_node_count           = 8
  scale_down_cooldown_time = 300
  type                     = "vm"

  root_volume {
    size       = 50
    volumetype = "SSD"
  }

  data_volumes {
    size       = 100
    volumetype = "SSD"
  }

  labels = {
    workload = "aiops"
  }

  tags = local.common_tags
}
