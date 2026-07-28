# Huawei Cloud Deployment

## Deployment status

The repository is **Huawei Cloud deployment-ready**. Local code, configuration,
tests, Helm rendering, and Terraform syntax can be validated without cloud
credentials. Creating CCE, SWR, OBS, AOM, LTS, or billable resources requires an
authorized Huawei Cloud account and an explicit `terraform apply`.

## Target services

- Cloud Container Engine (CCE)
- Software Repository for Container (SWR)
- Application Operations Management (AOM 2.0)
- Log Tank Service (LTS)
- Object Storage Service (OBS)
- Cloud Eye and Simple Message Notification where required

## Procedure

1. Review regional CCE version, flavor, quota, and projected cost.
2. Configure Huawei Cloud provider credentials through approved environment or
   workload-identity mechanisms.
3. Copy `terraform/terraform.tfvars.example` to an untracked `terraform.tfvars`.
4. Run `terraform init`, `fmt`, `validate`, and `plan`.
5. Apply only after plan review and change approval.
6. Build four images and push immutable tags/digests to the provisioned SWR
   repositories.
7. Install CCE Cloud Native Cluster Monitoring and Cloud Native Log Collection.
8. Connect CCE metrics to AOM and application logs to LTS.
9. Update Helm registry and image tag values.
10. Deploy with an atomic Helm upgrade and verify probes, dashboards, SLOs, and
    dry-run incident decisions.

## Example Helm command

```bash
helm upgrade --install aiops helm/huawei-aiops \
  --namespace huawei-aiops \
  --create-namespace \
  --values helm/huawei-aiops/values-huawei-cloud.yaml \
  --set image.registry="$SWR_REGISTRY" \
  --set image.tag="$IMAGE_TAG" \
  --atomic \
  --timeout 10m
```

## AOM and LTS

Huawei Cloud AOM provides unified observability across metrics, logs, and
traces, while CCE exposes cloud-native monitoring and log-collection add-ons.
Follow the current regional console and official documentation:

- [AOM service overview](https://support.huaweicloud.com/intl/en-us/productdesc-aom2/aom_01_0001.html)
- [Connect running environments to AOM](https://support.huaweicloud.com/intl/en-us/usermanual-aom2/mon_01_0197.html)
- [CCE observability overview](https://support.huaweicloud.com/intl/en-us/usermanual-cce/cce_10_0110.html)
- [CCE Cloud Native Log Collection](https://support.huaweicloud.com/intl/en-us/usermanual-cce/cce_10_0416.html)

## Production readiness gates

- private CCE endpoint or approved access boundary;
- IAM least privilege and key rotation;
- private SWR repositories and image signing;
- encrypted storage and retention;
- NetworkPolicy enforcement;
- backup and restore tests;
- alert ownership and notification routing;
- active automation change approval;
- capacity and failure testing.
