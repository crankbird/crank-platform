# Repository Organization Strategy

**Type**: Strategic Proposal
**Status**: Draft
**Temporal Context**: Future Direction (Potential Refactor)
**Last Updated**: November 14, 2025
**Purpose**: Proposed multi-repository structure for infrastructure separation

## 📁 **Recommended Structure**

Based on industry best practices and your growing infrastructure needs:

### **crank-platform/** (Core Application)

```text
crank-platform/
├── src/                     # Application source code
├── tests/                   # Application tests
├── docs/                    # Application documentation
├── docker/                  # Application Dockerfiles
│   ├── Dockerfile.platform
│   ├── Dockerfile.worker
│   └── Dockerfile.dev
├── .github/
│   └── workflows/
│       └── test-and-build.yml  # Application CI only
├── requirements.txt
├── pyproject.toml
└── README.md

```

### **crank-infrastructure/** (DevOps & Infrastructure)

```text
crank-infrastructure/
├── development-environments/
│   ├── dev-universal.sh           # Cross-platform dev script
│   ├── docker-compose.development.yml   # Complete dev environment with CA
│   ├── docker-compose.local.yml   # Local development
│   ├── .env.local.template        # Local env template
│   ├── .env.dev.template          # Shared dev env template
│   └── README.md                  # Local dev documentation
├── deployment/
│   ├── azure/
│   │   ├── deploy-azure.sh        # Azure deployment automation
│   │   ├── docker-compose.azure.yml
│   │   ├── .env.azure.template
│   │   ├── acr-setup.sh           # Azure Container Registry setup
│   │   └── aci-deploy.yml         # Azure Container Instance config
│   ├── aws/                       # Future AWS deployment
│   │   ├── deploy-aws.sh
│   │   ├── docker-compose.aws.yml
│   │   └── cloudformation/
│   ├── gcp/                       # Future GCP deployment
│   │   ├── deploy-gcp.sh
│   │   ├── docker-compose.gcp.yml
│   │   └── terraform/
│   └── kubernetes/                # Future K8s deployment
│       ├── manifests/
│       ├── helm-charts/
│       └── kustomize/
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts.yml
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── datasources/
│   ├── logs/
│   │   ├── fluentd/
│   │   ├── elasticsearch/
│   │   └── kibana/
│   └── docker-compose.monitoring.yml
├── security/
│   ├── vulnerability-scanning/
│   ├── secrets-management/
│   ├── ssl-certificates/
│   └── compliance/
├── scripts/
│   ├── setup-dev-environment.sh   # Cross-platform dev setup
│   ├── cleanup-registry.sh        # ACR maintenance
│   ├── health-check.sh            # Universal health checks
│   ├── backup-volumes.sh          # Data backup automation
│   └── restore-volumes.sh         # Data restore automation
├── .github/
│   └── workflows/
│       ├── deploy-infrastructure.yml  # Infrastructure CI/CD
│       ├── security-scan.yml          # Security scanning
│       └── cleanup-resources.yml      # Resource cleanup
├── terraform/                     # Infrastructure as Code
│   ├── modules/
│   ├── environments/
│   └── providers/
└── ansible/                       # Configuration Management
    ├── playbooks/
    ├── roles/
    └── inventory/

```

## 🎯 **Why This Structure?**

### **Separation of Concerns**

- **crank-platform**: Focus on application code, features, and business logic

- **crank-infrastructure**: Focus on deployment, operations, and DevOps

### **Team Scalability**

- **Developers** primarily work in `crank-platform`

- **DevOps/SRE** primarily work in `crank-infrastructure`

- **Clear ownership** and responsibility boundaries

### **Deployment Independence**

- Application releases don't require infrastructure changes

- Infrastructure updates don't affect application CI/CD

- Different teams can move at different speeds

### **Multi-Environment Support**

- Easy to add new cloud providers

- Environment-specific configurations isolated

- Consistent deployment patterns across platforms

## 🚀 **Migration Plan**

### **Phase 1: Extract Infrastructure** ✅ *Ready to Execute*

```bash
# 1. Create crank-infrastructure repository

git clone <new-crank-infrastructure-repo>

# 2. Move infrastructure files

cp -r .github/workflows/build-and-deploy.yml → crank-infrastructure/.github/workflows/
cp dev-universal.sh → crank-infrastructure/development-environments/
cp docker-compose.*.yml → crank-infrastructure/development-environments/
cp deploy-azure.sh → crank-infrastructure/deployment/azure/
cp .env.*.template → crank-infrastructure/development-environments/

# 3. Update crank-platform

# Keep only: src/, tests/, docs/, basic Dockerfiles, app-specific CI

```

### **Phase 2: Enhance Infrastructure**

- Add monitoring stack (Prometheus/Grafana)

- Implement Terraform for infrastructure as code

- Add security scanning and compliance

- Create backup/restore automation

### **Phase 3: Multi-Cloud Support**

- AWS deployment scripts

- GCP deployment scripts

- Kubernetes manifests

- Helm charts for container orchestration

- Kubernetes manifests

- Helm charts for container orchestration

## 📋 **Cross-Platform Compatibility Matrix**

| Tool/Script | macOS | Linux | WSL2 | Notes |
|-------------|-------|-------|------|-------|
| dev-universal.sh | ✅ | ✅ | ✅ | Platform detection & adaptive commands |
| Docker Compose | ✅ | ✅ | ✅ | Native support everywhere |
| Health Checks | ✅ | ✅ | ✅ | curl-based, universal |
| Azure CLI | ✅ | ✅ | ✅ | Optional dependency |
| Watch Command | ✅ | ⚠️ | ⚠️ | Install separately on some Linux distros |

### **Key Improvements in dev-universal.sh:**

1. **Platform Detection**: Automatically detects macOS/Linux/WSL2

2. **Adaptive Installation Instructions**: Platform-specific guidance

3. **Flexible Docker Compose**: Supports both `docker-compose` and `docker compose`

4. **Graceful Degradation**: Works even without optional tools like `watch`

5. **Universal Error Messages**: No platform-specific assumptions

## 🎉 **Benefits of This Approach**

### **For Developers**

- **Simple setup**: One script works everywhere

- **Consistent experience**: Same commands across all platforms

- **Clear documentation**: Platform-specific guidance when needed

### **For DevOps**

- **Centralized infrastructure**: All deployment logic in one place

- **Version controlled**: Infrastructure changes tracked like code

- **Reusable patterns**: Deploy to multiple clouds with same patterns

### **For Organization**

- **Scalable**: Easy to add new environments and teams

- **Maintainable**: Clear separation reduces complexity

- **Secure**: Dedicated security and compliance workflows

## 🚀 **Next Steps**

1. **Create `crank-infrastructure` repository**

2. **Move `dev-universal.sh` to infrastructure repo**

3. **Update documentation with new repository structure**

4. **Test cross-platform compatibility on different Linux distros**

5. **Implement infrastructure CI/CD pipeline**

This structure sets you up for **enterprise-scale growth** while maintaining **developer productivity**! 🎯
