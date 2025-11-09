# 🚀 Azure Container Deployment Guide

This guide will help you deploy the security-enhanced Crank Platform to your Azure environment.

## 📋 Prerequisites

✅ **Azure CLI** installed and logged in
✅ **Docker** running locally  
✅ **Azure Container Registry** access (`crankplatformregistry.azurecr.io`)
✅ **Azure subscription** with Container Instance permissions

## 🎯 Quick Deployment

### Option 1: Automated Script (Recommended)

```bash
# Run the automated deployment script

./deploy-azure.sh

```

### Option 2: Manual Azure Container Instance

```bash
# 1. Set environment variables

export RESOURCE_GROUP="crank-platform"
export LOCATION="australiaeast"
export CONTAINER_GROUP="crank-platform-prod"

# 2. Create resource group (if needed)

az group create --name $RESOURCE_GROUP --location $LOCATION

# 3. Deploy with Docker Compose for Azure

az container create \
  --resource-group $RESOURCE_GROUP \
  --file docker-compose.azure.yml \
  --dns-name-label crank-platform-prod

```

### Option 3: Azure Container Apps (Serverless)

```bash
# 1. Create Container Apps environment

az containerapp env create \
  --name crank-platform-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# 2. Deploy platform service

az containerapp create \
  --name crank-platform \
  --resource-group $RESOURCE_GROUP \
  --environment crank-platform-env \
  --image crankplatformregistry.azurecr.io/crank-platform:latest \
  --target-port 8443 \
  --ingress 'external' \
  --env-vars CRANK_ENVIRONMENT=production PLATFORM_HTTPS_PORT=8443

```

## 🔧 Configuration

### Environment Variables

Copy `.env.azure` to `.env` and update:

```bash
# Copy Azure configuration

cp .env.azure .env

# Edit for your environment

nano .env

```

Key settings to update:

- `PLATFORM_AUTH_TOKEN` - Generate secure token

- `AZURE_SUBSCRIPTION_ID` - Your subscription ID

- `AZURE_RESOURCE_GROUP` - Your resource group name

### Port Configuration

The platform uses these port ranges:

- **Platform**: `8000` (HTTP), `8443` (HTTPS)

- **Document Converter**: `8100-8101`

- **Email Classifier**: `8200-8201`

- **Email Parser**: `8300-8301`

- **Image Classifier**: `8400-8401`

- **Streaming**: `8500-8501`

## 🧪 Testing Deployment

### Health Check Commands

```bash
# Get deployment FQDN

FQDN=$(az container show --resource-group crank-platform --name crank-platform-prod --query ipAddress.fqdn --output tsv)

# Test platform health

curl -k "https://$FQDN:8443/health/live"

# Test worker registration

curl -k -H "Authorization: Bearer your-auth-token" "https://$FQDN:8443/v1/workers"

```

### Monitoring Commands

```bash
# View container logs

az container logs --resource-group crank-platform --name crank-platform-prod

# Check container status

az container show --resource-group crank-platform --name crank-platform-prod

# Monitor metrics

az monitor metrics list --resource /subscriptions/YOUR_SUB/resourceGroups/crank-platform/providers/Microsoft.ContainerInstance/containerGroups/crank-platform-prod

```

## 🔒 Security Features Deployed

✅ **Input Sanitization** - Wendy's security framework active
✅ **mTLS Communication** - All services use HTTPS
✅ **Pattern Validation** - Oliver's security checks running
✅ **Environment-based Config** - Kevin's port management
✅ **Zero-trust Architecture** - Authentication required

## 🚨 Troubleshooting

### Common Issues

**Container fails to start:**

```bash
# Check logs for errors

az container logs --resource-group crank-platform --name crank-platform-prod

# Check container events

az container show --resource-group crank-platform --name crank-platform-prod --query instanceView

```

**Port conflicts:**

```bash
# Verify port configuration in .env

cat .env | grep PORT

# Check Azure networking

az container show --resource-group crank-platform --name crank-platform-prod --query ipAddress

```

**Authentication errors:**

```bash
# Verify auth token

echo $PLATFORM_AUTH_TOKEN

# Test with correct headers

curl -k -H "Authorization: Bearer $PLATFORM_AUTH_TOKEN" "https://$FQDN:8443/v1/workers"

```

## 📊 Cost Optimization

### Azure Container Instances Pricing

- **CPU**: 4 cores × $0.0012/hour = ~$35/month

- **Memory**: 8GB × $0.00015/hour = ~$9/month

- **Total**: ~$44/month for full platform

### Cost Reduction Options

1. **Reduce CPU/Memory** for dev environments

2. **Use Container Apps** for automatic scaling

3. **Schedule shutdown** for non-production instances

## 🔄 Updates & Maintenance

### Updating Images

```bash
# Rebuild and push updated images

docker-compose -f docker-compose.multi-worker.yml build
docker tag crank-platform-platform:latest crankplatformregistry.azurecr.io/crank-platform:latest
docker push crankplatformregistry.azurecr.io/crank-platform:latest

# Restart container instance

az container restart --resource-group crank-platform --name crank-platform-prod

```

### Backup & Recovery

```bash
# Export container configuration

az container export --resource-group crank-platform --name crank-platform-prod

# Create resource group template

az group export --name crank-platform

```

## 🎯 Next Steps

1. **Deploy** using `./deploy-azure.sh`

2. **Test** all endpoints and functionality

3. **Configure** monitoring and alerts

4. **Set up** CI/CD pipeline for updates

5. **Scale** additional worker instances as needed

For support, check the logs and use the troubleshooting commands above!
