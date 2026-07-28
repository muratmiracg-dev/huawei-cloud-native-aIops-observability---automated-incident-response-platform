variable "region" {
  description = "Huawei Cloud region in which resources are created."
  type        = string
  default     = "tr-west-1"
}

variable "availability_zone" {
  description = "Availability zone for CCE worker nodes."
  type        = string
  default     = "tr-west-1a"
}

variable "project_name" {
  description = "Resource-name prefix."
  type        = string
  default     = "huawei-aiops"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,24}$", var.project_name))
    error_message = "project_name must be 3-25 lowercase alphanumeric or hyphen characters."
  }
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "portfolio"

  validation {
    condition     = contains(["dev", "test", "staging", "production", "portfolio"], var.environment)
    error_message = "environment must be dev, test, staging, production, or portfolio."
  }
}

variable "vpc_cidr" {
  description = "VPC CIDR."
  type        = string
  default     = "10.42.0.0/16"
}

variable "subnet_cidr" {
  description = "CCE node subnet CIDR."
  type        = string
  default     = "10.42.10.0/24"
}

variable "subnet_gateway" {
  description = "CCE node subnet gateway."
  type        = string
  default     = "10.42.10.1"
}

variable "cluster_flavor" {
  description = "CCE control-plane flavor."
  type        = string
  default     = "cce.s1.small"
}

variable "cluster_version" {
  description = "CCE Kubernetes version. Confirm regional availability before apply."
  type        = string
  default     = "v1.31"
}

variable "node_flavor" {
  description = "CCE worker-node flavor."
  type        = string
  default     = "s7n.large.2"
}

variable "node_os" {
  description = "CCE worker-node operating system."
  type        = string
  default     = "Huawei Cloud EulerOS 2.0"
}

variable "key_pair_name" {
  description = "Existing Huawei Cloud key-pair name for worker nodes."
  type        = string
}

variable "initial_node_count" {
  description = "Initial number of CCE workers."
  type        = number
  default     = 2

  validation {
    condition     = var.initial_node_count >= 1 && var.initial_node_count <= 10
    error_message = "initial_node_count must be between 1 and 10."
  }
}

variable "swr_organization" {
  description = "Globally unique SWR organization name."
  type        = string
}

variable "observability_bucket_name" {
  description = "Globally unique private OBS bucket for exported observability data."
  type        = string
}
