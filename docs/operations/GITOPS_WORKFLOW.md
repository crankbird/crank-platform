# 🚀 GitOps Container Workflow

This document explains our complete GitOps setup using Azure Container Registry as the central artifact repository for multi-environment deployments.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌────────────────────┐    ┌─────────────────┐
│   Local Dev     │    │  Azure Container   │    │  Azure Prod     │
│  (MacBook)      │    │     Registry       │    │ (Container Inst)│
│                 │    │                    │    │                 │
│ Docker Desktop  │◄──►│  Multi-platform    │◄──►│   Production    │
│ Apple Silicon   │    │     Images         │    │   Deployment    │
│ Intel x86       │    │  ARM64 + AMD64     │    │                 │
└─────────────────┘    └────────────────────┘    └─────────────────┘
        ▲                        ▲                        ▲
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                    ┌────────────────────┐
                    │   GitHub Actions   │
                    │                    │
                    │ • Build & Test     │
                    │ • Security Scan    │
                    │ • Multi-platform   │
                    │ • Auto Deploy      │
                    └────────────────────┘
```

## 🎯 Why Azure Container Registry?

### ✅ **Advantages over GitHub Packages/LFS:**

1. **Multi-Platform Support**: Native ARM64 + AMD64 images
2. **Docker Integration**: `docker pull/push` works seamlessly
3. **Layer Deduplication**: Massive storage savings
4. **Global CDN**: Fast pulls worldwide
5. **Security**: Vulnerability scanning, RBAC
6. **Cost Effective**: ~$0.10/GB/month vs GitHub's $0.25/GB
7. **No Size Limits**: Unlike GitHub's 2GB file limit

### ❌ **GitHub LFS Problems:**

- **No Docker Native Support** - Manual download/load process
- **Expensive** - $5/month for 50GB vs ACR $5/month for 50GB + CDN
- **No Layer Sharing** - Each image is monolithic
- **Size Limits** - 2GB per file maximum

## 🔄 GitOps Workflow

### 1. **Development Workflow**

```bash
# On your MacBook - make changes
git add .
git commit -m "Add new feature"
git push origin feature-branch

# GitHub Actions automatically:
# 1. Detects changed services
# 2. Builds multi-platform images  
# 3. Runs security scans
# 4. Pushes to Azure Container Registry
# 5. Updates deployment (if main branch)
```

### 2. **Automated CI/CD Pipeline**

```yaml
# .github/workflows/build-and-deploy.yml does:

📋 Change Detection → Only build changed services
🏗️ Multi-Platform Build → ARM64 (Mac) + AMD64 (Azure)  
🔍 Security Scanning → Trivy vulnerability scan
📦 Registry Push → crankplatformregistry.azurecr.io
🚀 Auto Deploy → Azure Container Instances (main branch)
🧪 Integration Tests → Health checks + API tests
```

### 3. **Multi-Environment Strategy**

| Environment | Branch | Trigger | Registry Tag | Deployment |
|-------------|--------|---------|--------------|------------|
| **Local Dev** | any | manual | `latest` | Docker Desktop |
| **Staging** | `develop` | auto | `develop-{sha}` | Azure Container Instances |
| **Production** | `main` | auto | `latest` + `main-{sha}` | Azure Container Instances |

## 🍎 Local MacBook Development

### **Initial Setup:**
```bash
# 1. Clone repository
git clone https://github.com/crankbird/crank-platform.git
cd crank-platform

# 2. Setup local environment
./dev-local.sh setup

# 3. Start services (pulls from ACR automatically)
./dev-local.sh start
```

### **Daily Development:**
```bash
# Quick start
./dev-local.sh start

# Lightweight start (no ML services)
./dev-local.sh start-min

# View logs
./dev-local.sh logs

# Test everything
./dev-local.sh test

# Update to latest images
./dev-local.sh update
```

### **Multi-Platform Image Support**

Your MacBook will automatically pull the correct architecture:
- **Apple Silicon (M1/M2)**: Uses `linux/arm64` images
- **Intel Mac**: Uses `linux/amd64` images
- **Performance**: Native architecture = better performance

## 🚀 Azure Production Deployment

### **Automatic Deployment:**
```bash
# Push to main branch triggers auto-deployment
git checkout main
git merge feature-branch
git push origin main

# GitHub Actions automatically:
# 1. Builds & tests images
# 2. Pushes to ACR
# 3. Deploys to Azure Container Instances
# 4. Runs integration tests
```

### **Manual Deployment:**
```bash
# Use the deployment script
./deploy-azure.sh

# Or trigger via GitHub Actions
gh workflow run build-and-deploy.yml -f deploy_environment=production
```

## 📦 Container Registry Management

### **Image Naming Convention:**
```
crankplatformregistry.azurecr.io/[service]:[tag]

Examples:
- crankplatformregistry.azurecr.io/crank-platform:latest
- crankplatformregistry.azurecr.io/crank-platform:main-abc1234
- crankplatformregistry.azurecr.io/crank-doc-converter:develop-def5678
```

### **Managing Images:**
```bash
# List all images
az acr repository list --name crankplatformregistry

# List tags for a service
az acr repository show-tags --name crankplatformregistry --repository crank-platform

# Delete old images (cost optimization)
az acr repository delete --name crankplatformregistry --image crank-platform:old-tag

# Repository cleanup (keep latest 10 tags)
az acr repository show-tags --name crankplatformregistry --repository crank-platform \
  --orderby time_desc --output table | tail -n +11 | \
  xargs -I {} az acr repository delete --name crankplatformregistry --image crank-platform:{}
```

## 🔒 Security & Access

### **GitHub Secrets Required:**
```bash
AZURE_CREDENTIALS          # Service principal for deployment
AZURE_CLIENT_ID            # ACR authentication  
AZURE_CLIENT_SECRET        # ACR authentication
PLATFORM_AUTH_TOKEN        # Platform API authentication
```

### **Local Development Access:**
```bash
# One-time setup for ACR access
az login
az acr login --name crankplatformregistry

# Docker automatically uses these credentials
docker pull crankplatformregistry.azurecr.io/crank-platform:latest
```

## 📊 Cost Optimization

### **Azure Container Registry:**
- **Basic SKU**: $5/month for 10GB storage
- **Storage**: $0.10/GB/month additional
- **Bandwidth**: Free egress to Azure regions

### **Optimization Strategies:**

1. **Image Cleanup**: Delete old tags automatically
2. **Multi-stage Builds**: Smaller final images
3. **Layer Caching**: Faster builds, less storage
4. **Scheduled Deletion**: Keep only recent tags

```bash
# Weekly cleanup script
az acr repository show-tags --name crankplatformregistry --repository crank-platform \
  --orderby time_desc --output tsv | tail -n +6 | \
  xargs -I {} az acr repository delete --name crankplatformregistry --image crank-platform:{} --yes
```

## 🧪 Testing Strategy

### **Automated Testing:**
- **Unit Tests**: In build pipeline
- **Security Scans**: Trivy vulnerability scanning  
- **Integration Tests**: Live endpoint testing
- **Health Checks**: Kubernetes-style health endpoints

### **Local Testing:**
```bash
# Test all endpoints
./dev-local.sh test

# Manual endpoint testing
curl -k https://localhost:8443/health/live
curl -k https://localhost:8201/health
```

### **Production Testing:**
```bash
# GitHub Actions runs these automatically
curl -k https://crank-platform-prod.australiaeast.azurecontainer.io:8443/health/live
```

## 🔄 Rollback Strategy

### **Automated Rollback:**
```bash
# Tag previous working version as latest
az acr import --name crankplatformregistry \
  --source crankplatformregistry.azurecr.io/crank-platform:main-abc1234 \
  --image crank-platform:latest

# Restart Azure Container Instance
az container restart --name crank-platform-prod --resource-group crank-platform
```

### **Local Rollback:**
```bash
# Use specific tag
export TAG=main-abc1234
./dev-local.sh start
```

## 📈 Monitoring & Observability

### **Container Insights:**
- Azure Monitor integration
- Real-time metrics and logs
- Custom dashboards

### **Health Monitoring:**
```bash
# Check all container health
az container show --name crank-platform-prod --resource-group crank-platform \
  --query "containers[].instanceView.currentState"

# View logs
az container logs --name crank-platform-prod --resource-group crank-platform
```

## 🚀 Next Steps

1. **✅ Commit GitOps configuration**
2. **✅ Setup GitHub secrets** 
3. **✅ Test local development workflow**
4. **✅ Deploy to Azure using automated pipeline**
5. **✅ Setup monitoring and alerts**

This GitOps approach gives you:
- **🔄 Automated deployments**
- **🍎 Native MacBook development**
- **🏗️ Multi-platform support**
- **💰 Cost-effective artifact storage**
- **🔒 Enterprise security**
- **📊 Full observability**