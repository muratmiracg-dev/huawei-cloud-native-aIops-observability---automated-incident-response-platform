output "cce_cluster_id" {
  description = "CCE cluster identifier."
  value       = huaweicloud_cce_cluster.platform.id
}

output "cce_cluster_name" {
  description = "CCE cluster name."
  value       = huaweicloud_cce_cluster.platform.name
}

output "swr_login_server" {
  description = "SWR registry login server."
  value       = huaweicloud_swr_organization.platform.login_server
}

output "swr_repository_paths" {
  description = "Private SWR repository paths."
  value       = { for name, repository in huaweicloud_swr_repository.services : name => repository.path }
}

output "observability_bucket" {
  description = "OBS bucket for retained observability exports."
  value       = huaweicloud_obs_bucket.observability.bucket
}

output "next_steps" {
  description = "Post-provisioning deployment guidance."
  value = [
    "Install Cloud Native Cluster Monitoring and Cloud Native Log Collection add-ons in CCE.",
    "Configure AOM and LTS ingestion according to docs/huawei-cloud-deployment.md.",
    "Push signed images to the output SWR repositories.",
    "Deploy helm/huawei-aiops with values-huawei-cloud.yaml.",
  ]
}
