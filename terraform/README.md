# Huawei Cloud infrastructure

This Terraform stack provisions the cloud foundation used by the reference
platform:

- isolated VPC and CCE node subnet;
- RBAC-enabled Huawei Cloud CCE cluster;
- auto-scaling worker node pool;
- private Huawei Cloud SWR organization and four service repositories;
- versioned private OBS bucket with lifecycle controls.

## Authentication

Use the standard Huawei Cloud provider environment variables. Never place access
keys in `terraform.tfvars`, source control, shell history, or CI logs.

## Validate

```bash
terraform init -backend=false
terraform fmt -check -recursive
terraform validate
```

## Plan

```bash
cp terraform.tfvars.example terraform.tfvars
terraform plan -out=platform.tfplan
```

Review regional CCE versions, node flavors, service quotas, and projected cost
before applying. This repository does not automatically run `terraform apply`.
