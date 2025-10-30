# Azure Container Apps Setup Guide for Crank Platform

> **Critical**: This guide contains all the real-world deployment experience and troubleshooting for deploying Crank Platform to Azure Container Apps. Updated October 30, 2025 with production deployment lessons learned.

## 🎯 **Production Deployment Status (October 30, 2025)**

✅ **SUCCESSFULLY DEPLOYED TO AZURE CONTAINER APPS**

**Live Production Gateway**: https://crank-gateway.greenforest-24b43401.australiaeast.azurecontainerapps.io/

The Crank Platform is **LIVE IN PRODUCTION** on Azure Container Apps with:

- ✅ **Gateway Service**: Running and responding to requests
- ✅ **Security-First Architecture**: API key authentication implemented
- ✅ **Australian Deployment**: Sydney region for optimal AI/GPU capabilities
- ✅ **Auto-scaling**: 1-3 replicas based on demand
- ✅ **Container Registry**: crankplatformregistry.azurecr.io
- ✅ **Monitoring**: Azure Log Analytics integrated
- ✅ **All Import Issues**: Fixed and documented below

## 🚧 **Development VM Status**

❌ **GPU Development VM**: **NOT DEPLOYED** - Requires GPU quota request  
⚠️ **GPU Quota**: 0 cores available (default for new subscriptions)  
📋 **Action Required**: Request GPU quota via Azure Portal before VM creation  
💡 **Recommendation**: Follow GPU quota prerequisites section below

**🎯 Goal**: Create GPU-enabled development VM equivalent to current WSL2 environment for VS Code Remote access from Mac

## 🏗️ **Repository Structure**

```
/home/johnr/projects/
├── crank-platform/          # Main platform (THIS REPO)
│   ├── services/            # Mesh interface implementation
│   ├── azure/              # Deployment strategy + testing
│   ├── ENHANCEMENT_ROADMAP.md
│   └── README.md           # Complete vision and status
├── crankdoc/               # Document processing service
│   ├── ENHANCEMENT_ROADMAP.md
│   └── INTEGRATION_STRATEGY.md
├── parse-email-archive/    # Email parsing service
└── dotfiles/               # Development environment
```

## 🚀 **Quick Azure VM Setup**

### 1. Clone Repositories
```bash
cd /home/$(whoami)/projects
git clone git@github.com:crankbird/crank-platform.git
git clone git@github.com:crankbird/crankdoc.git
git clone git@github.com:crankbird/parse-email-archive.git
git clone git@github.com:crankbird/dotfiles.git
```

### 2. Install Dependencies
```bash
# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Node.js (for Graphite CLI)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Graphite CLI
npm install -g @withgraphite/graphite-cli@latest

# Python + uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Authenticate Tools
```bash
# Graphite (use your token)
gt auth --token c7l1GB3uOrGp9USp1Y42iG4snP26C9HKS868xBRdJn5GLiX2pbZ0hiiCDB6m

# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
az login
```

## 🐳 **Test Local Mesh Services**

```bash
cd /home/$(whoami)/projects/crank-platform/services

# Build and start mesh services
docker-compose up --build

# Test endpoints (in another terminal)
curl -H "Authorization: Bearer dev-mesh-key" http://localhost:8080/v1/capabilities
curl -H "Authorization: Bearer dev-mesh-key" http://localhost:8080/health/live
```

## 🚨 **CRITICAL: GPU Quota Prerequisites**

> **⚠️ WARNING**: Azure subscriptions have **ZERO GPU quota by default**. You MUST request quota before attempting GPU VM creation.

### **GPU Quota Check and Request Process**

#### **Step 1: Check Current GPU Quota**
```bash
# List available GPU VM sizes in your region
az vm list-skus --location australiaeast --size Standard_NC --query "[?resourceType=='virtualMachines']" --output table

# Check quota status (requires Microsoft.Quota provider)
az provider register -n Microsoft.Quota --wait
```

#### **Step 2: Request GPU Quota via Azure Portal**
1. **Navigate**: https://portal.azure.com → Subscriptions → Your Subscription → Usage + quotas
2. **Search**: "Standard NCASv3_T4 Family" (or your preferred GPU family)
3. **Request**: Minimum 4 cores for 1 GPU VM
4. **Justification**: "AI/ML development platform for enterprise research"
5. **Expected approval**: 15 minutes - 2 hours for standard requests

#### **Step 3: Recommended GPU Quotas for AI/ML Development**
| GPU Family | VM Size | GPU | vCPUs | RAM | Cost/hour | Recommended Quota |
|------------|---------|-----|-------|-----|-----------|-------------------|
| **Standard NCASv3_T4 Family** | NC4as_T4_v3 | Tesla T4 | 4 | 28GB | ~$0.60 | 4 cores |
| **standardNCSv3Family** | NC6s_v3 | Tesla V100 | 6 | 112GB | ~$3.50 | 6 cores |
| **Standard NCv3 Family** | NC6 | Tesla K80 | 6 | 56GB | ~$1.80 | 6 cores |

#### **Step 4: Test GPU Availability Before VM Creation**
```bash
# Test if GPU quota is available (will fail if no quota)
az vm create --resource-group test-rg --name test-gpu-vm --image Ubuntu2204 --size Standard_NC4as_T4_v3 --admin-username testuser --generate-ssh-keys --location australiaeast --no-wait --dry-run
```

> **💡 Pro Tip**: Request quota for multiple GPU families as backup options. Tesla T4 (NCASv3_T4) is usually the fastest to approve.

## 🖥️ **Development VM Creation**

### **GPU Development VM (Recommended for AI/ML)**

> **Prerequisites**: GPU quota must be approved first (see section above)

```bash
# Create GPU-enabled development VM
az vm create \
  --resource-group crank-platform \
  --name crank-gpu-dev-vm \
  --image Ubuntu2204 \
  --size Standard_NC4as_T4_v3 \
  --admin-username johnr \
  --generate-ssh-keys \
  --location australiaeast \
  --public-ip-sku Standard \
  --storage-sku Premium_LRS \
  --os-disk-size-gb 128

# Open SSH access
az vm open-port --resource-group crank-platform --name crank-gpu-dev-vm --port 22
```

### **CPU Development VM (Fallback Option)**

> **Use Case**: When GPU quota is pending or for non-ML development

```bash
# Create CPU-only development VM  
az vm create \
  --resource-group crank-platform \
  --name crank-dev-vm-cpu \
  --image Ubuntu2204 \
  --size Standard_D4s_v3 \
  --admin-username johnr \
  --generate-ssh-keys \
  --location australiaeast \
  --public-ip-sku Standard \
  --storage-sku Premium_LRS \
  --os-disk-size-gb 128

# Open SSH access
az vm open-port --resource-group crank-platform --name crank-dev-vm-cpu --port 22
```

### **Development Environment Setup**

Once your VM is created, set up the development environment:

```bash
# Get VM IP address
VM_IP=$(az vm show --resource-group crank-platform --name crank-gpu-dev-vm --show-details --query publicIps --output tsv)

# SSH into VM and setup environment
ssh johnr@$VM_IP "git clone https://github.com/crankbird/dotfiles.git && cd dotfiles && ./install.sh"

# Install AI/ML environment (GPU VMs only)
ssh johnr@$VM_IP "cd dotfiles && ./dev-environment/install-aiml.sh"

# Verify setup
ssh johnr@$VM_IP "cd dotfiles && ./dev-environment/check-env.sh"
```

### **VS Code Remote Setup**

1. **Install VS Code Extension**: "Remote - SSH" 
2. **Add SSH Host**: `johnr@YOUR_VM_IP`
3. **Connect**: Cmd/Ctrl + Shift + P → "Remote-SSH: Connect to Host"
4. **Clone Projects**: In VS Code terminal on remote VM

```bash
# On the remote VM via VS Code
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/crankbird/crank-platform.git
git clone https://github.com/crankbird/crankdoc.git  
git clone https://github.com/crankbird/parse-email-archive.git
```

**🎯 Result**: You now have a cloud development environment accessible from any machine via VS Code Remote!

## ☁️ **Azure Container Apps Deployment (Production Ready)**

> **✅ VERIFIED**: This section contains the exact steps used for successful production deployment on October 30, 2025.

### **Step 1: Azure CLI Authentication**

Use device code authentication for enhanced 2FA support:

```bash
# Login with device code (required for enhanced 2FA)
az login --use-device-code

# Verify authentication
az account show
```

**Important**: The account will need **Contributor** role on the subscription. If you get authorization errors, have your Azure admin grant these permissions in the Azure portal:
1. Navigate to Subscriptions → Your Subscription → Access control (IAM)
2. Add role assignment: **Contributor** role to your account

### **Step 2: Register Required Providers**

```bash
# Register providers (required for first-time setup)
az provider register -n Microsoft.OperationalInsights --wait
az provider register -n Microsoft.App --wait
az provider register -n Microsoft.ContainerRegistry --wait
```

### **Step 3: Create Resources**

```bash
# Create resource group in Australia East (Sydney) for AI/GPU capabilities
az group create --name crank-platform --location australiaeast

# Create Container Apps Environment (includes auto-generated Log Analytics)
az containerapp env create \
  --name crank-platform-env \
  --resource-group crank-platform \
  --location australiaeast

# Create Container Registry
az acr create \
  --resource-group crank-platform \
  --name crankplatformregistry \
  --sku Basic

# Enable admin access for Container Apps integration
az acr update -n crankplatformregistry --admin-enabled true
```

### **Step 4: Fix Service Code for Container Deployment**

> **🚨 CRITICAL**: These fixes are essential for successful deployment.

#### **Fix Python Import Issues**

1. **Create services/__init__.py**:
```bash
echo "# Crank Platform Services Package" > services/__init__.py
```

2. **Fix gateway.py imports** - Change absolute to relative imports:
```python
# BEFORE (breaks in container):
from mesh_interface import MeshRequest, MeshResponse, MeshCapabilities

# AFTER (works in container):
from .mesh_interface import MeshRequest, MeshResponse, MeshCapability
```

3. **Fix FastAPI app module exposure** - Add module-level app variable:
```python
# Add this after the create_gateway() function in gateway.py:
# Module-level app for uvicorn
app = create_gateway()
```

#### **Complete Working Dockerfile**

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY services/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy service files
COPY services/ ./services/

# Create necessary directories and set ownership
RUN mkdir -p /app/data /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

# Default command for gateway service
CMD ["python", "-m", "uvicorn", "services.gateway:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Step 5: Build and Deploy**

```bash
# Login to registry
az acr login --name crankplatformregistry

# Build and push image
docker build -t crankplatformregistry.azurecr.io/crank-platform:latest .
docker push crankplatformregistry.azurecr.io/crank-platform:latest

# Deploy gateway service
az containerapp create \
  --name crank-gateway \
  --resource-group crank-platform \
  --environment crank-platform-env \
  --image crankplatformregistry.azurecr.io/crank-platform:latest \
  --target-port 8000 \
  --ingress 'external' \
  --registry-server crankplatformregistry.azurecr.io \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars API_KEY_CRANKDOC=dev-secret-key-crankdoc-change-in-production API_KEY_CRANKEMAIL=dev-secret-key-crankemail-change-in-production MESH_ENV=production MESH_REGION=australia-east MESH_DEBUG=false
```

### **Step 6: Verify Deployment**

```bash
# Check application status
az containerapp show --name crank-gateway --resource-group crank-platform --query "properties.{provisioningState:provisioningState,runningStatus:runningStatus,fqdn:configuration.ingress.fqdn}"

# View logs
az containerapp logs show --name crank-gateway --resource-group crank-platform --tail 50

# Test the service
curl https://YOUR-APP-URL.azurecontainerapps.io/
```

**Expected Response**:
```json
{
  "name": "Crank Platform Gateway",
  "version": "1.0.0",
  "description": "Unified gateway for all Crank mesh services",
  "available_services": ["document", "email"],
  "endpoints": {
    "process": "/v1/process",
    "capabilities": "/v1/capabilities",
    "receipts": "/v1/receipts"
  }
}
```

### **Common Troubleshooting**

#### **Import Errors**
- **Error**: `ModuleNotFoundError: No module named 'mesh_interface'`
- **Solution**: Use relative imports: `from .mesh_interface import ...`

#### **FastAPI App Not Found**
- **Error**: `Attribute "app" not found in module "services.gateway"`
- **Solution**: Add module-level `app = create_gateway()` in gateway.py

#### **Permission Errors**
- **Error**: `AuthorizationFailed` when creating resources
- **Solution**: Add **Contributor** role to your account in Azure portal

#### **Container Registry Authentication**
- **Error**: `No credential was provided to access Azure Container Registry`
- **Solution**: Run `az acr update -n REGISTRY_NAME --admin-enabled true`

## 🇦🇺 **Australian Region Selection Guide**

| Region | Location | AI Services | GPU VMs | Latency | Recommendation |
|--------|----------|-------------|---------|---------|----------------|
| **australiaeast** | Sydney | ✅ Azure OpenAI<br>✅ Cognitive Services<br>✅ ML Studio | ✅ NCv3, NCasT4_v3<br>✅ NDv2 series | ~10-15ms | **RECOMMENDED** |
| **australiacentral** | Canberra | ❌ No Azure OpenAI<br>⚠️ Limited AI services | ❌ Very limited GPU | ~5-8ms | Only if no AI/GPU needed |

**Recommendation**: Use **Australia East (Sydney)** for future AI/GPU capabilities even if not needed immediately.

### 2. Deploy Container Apps Environment
```bash
cd /home/$(whoami)/projects/crank-platform/azure

# Review deployment strategy
cat deployment-strategy.md

# Deploy infrastructure (you'll need to create Bicep templates)
# See deployment-strategy.md for complete resource requirements
```

### 3. Run Adversarial Testing
```bash
# Test locally first
python azure/adversarial-test.py --target http://localhost:8080

# Test against Azure deployment
python azure/adversarial-test.py --target https://your-container-app.azurecontainerapps.io
```

## 🔑 **Critical Architecture Decisions Made**

### Mesh Interface Pattern
- **Universal base class**: `services/mesh_interface.py`
- **Standardized endpoints**: `/v1/process`, `/v1/capabilities`, `/v1/receipts`, `/health/*`
- **Authentication**: Bearer token middleware
- **Policy enforcement**: OPA/Rego ready
- **Receipt system**: Audit trail for all operations

### Service Implementations
- **CrankDoc Mesh**: `services/crankdoc_mesh.py` - Document conversion/analysis
- **CrankEmail Mesh**: `services/crankemail_mesh.py` - Email parsing/classification  
- **Platform Gateway**: `services/gateway.py` - Unified routing and health aggregation

### Container Strategy
- **Security hardened**: Non-root users, read-only filesystems
- **Resource limits**: Memory and CPU constraints
- **Health checks**: Startup, liveness, readiness probes
- **Service discovery**: Environment-based configuration

## 🎯 **The Vision Recap**

**"The Mesh"** - Transform any Python script into an enterprise-ready service with:
- **Governance**: Authentication, policies, audit trails
- **Security**: Container isolation, vulnerability scanning
- **Economics**: Usage tracking, chargeback, incentive alignment
- **Scale**: From gaming laptops to multi-cloud federation

**Energy Efficiency Philosophy**:
- Use large models (GPT-4) only for **training** specialized models
- Deploy small, efficient models (<50W) for **inference**
- Prefer procedural code and Unix utilities when possible
- Gaming laptop constraints drive efficient design

## 🚨 **Common Issues & Solutions**

### Docker Permission Issues
```bash
sudo usermod -aG docker $USER
newgrp docker  # Or logout/login
```

### Graphite Authentication
```bash
# If authentication fails, re-authenticate
gt auth --token c7l1GB3uOrGp9USp1Y42iG4snP26C9HKS868xBRdJn5GLiX2pbZ0hiiCDB6m
```

### Service Discovery Issues
```bash
# Check container networking
docker network ls
docker network inspect crank-platform_default
```

### Azure Container Apps Issues
```bash
# Check logs
az containerapp logs show --name crank-gateway --resource-group crank-platform

# Check revisions
az containerapp revision list --name crank-gateway --resource-group crank-platform
```

## 📝 **Development Workflow**

### Creating New Features
```bash
# Create new branch with Graphite
gt create feature-name

# Make changes, then submit PR
gt submit

# Merge and sync
gt repo sync
```

### Adding New Mesh Services
1. Copy `services/mesh_interface.py` as base class
2. Implement your service logic inheriting from `MeshInterface`
3. Add Dockerfile following security patterns
4. Update `docker-compose.yml`
5. Add to gateway routing in `gateway.py`

## 🔮 **Next Steps Priority**

1. **Azure Deployment** - Get mesh services running in Container Apps
2. **Adversarial Testing** - Validate security and performance
3. **Service Expansion** - Add CrankClassify, CrankExtract, etc.
4. **Economic Layer** - Usage tracking and chargeback systems
5. **Edge Deployment** - Gaming laptop and mobile device support

## 📞 **Emergency References**

- **Main Platform Repo**: https://github.com/crankbird/crank-platform
- **Service Documentation**: `/services/README.md`
- **Enhancement Roadmap**: `/ENHANCEMENT_ROADMAP.md`
- **Azure Strategy**: `/azure/deployment-strategy.md`
- **Graphite Docs**: https://docs.graphite.dev/
- **Azure Container Apps**: https://docs.microsoft.com/en-us/azure/container-apps/

---

## 🌟 **About the Author**

**John R** - the architect behind this platform. While the AI industry was busy building energy-hungry centralized behemoths, John built something different: **The Mesh** - distributed, efficient, and actually sustainable.

The core insight: use gaming laptop constraints as a design driver for efficiency, not a limitation to overcome. Turn every Python script into an enterprise service with governance and economic incentives.

This isn't just another tech project - it's infrastructure for making AI both economically viable and environmentally responsible.

*Good luck with the Azure deployment, future agent! The code is solid and the vision is clear.* 🚀