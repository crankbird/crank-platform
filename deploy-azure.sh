#!/bin/bash

# 🚀 Azure Container Instance Deployment Script
# 
# This script deploys the Crank Platform to Azure Container Instances
# with proper networking, security, and configuration for production use.

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
echo_success() { echo -e "${GREEN}✅ $1${NC}"; }
echo_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
echo_error() { echo -e "${RED}❌ $1${NC}"; }

# Configuration
RESOURCE_GROUP="crank-platform"
LOCATION="australiaeast"
ACR_NAME="crankplatformregistry"
CONTAINER_GROUP="crank-platform-prod"
DNS_NAME="crank-platform-prod"

echo_info "🚀 Starting Azure Container Instance Deployment"

# Check if logged into Azure
echo_info "Checking Azure CLI authentication..."
if ! az account show > /dev/null 2>&1; then
    echo_error "Not logged into Azure CLI. Please run 'az login' first."
    exit 1
fi
echo_success "Azure CLI authenticated"

# Check if resource group exists
echo_info "Checking resource group: $RESOURCE_GROUP"
if ! az group show --name $RESOURCE_GROUP > /dev/null 2>&1; then
    echo_warning "Resource group $RESOURCE_GROUP not found. Creating..."
    az group create --name $RESOURCE_GROUP --location $LOCATION
    echo_success "Resource group $RESOURCE_GROUP created"
else
    echo_success "Resource group $RESOURCE_GROUP found"
fi

# Check if container registry exists and get credentials
echo_info "Getting Azure Container Registry credentials..."
ACR_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)
echo_success "ACR credentials obtained: $ACR_SERVER"

# Deploy platform container
echo_info "Deploying Crank Platform to Azure Container Instances..."

az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_GROUP \
    --location $LOCATION \
    --dns-name-label $DNS_NAME \
    --cpu 4 \
    --memory 8 \
    --restart-policy OnFailure \
    --registry-login-server $ACR_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --environment-variables \
        PLATFORM_ENV=azure \
        CRANK_ENVIRONMENT=production \
        LOG_LEVEL=INFO \
        PLATFORM_PORT=8000 \
        PLATFORM_HTTPS_PORT=8443 \
        AZURE_SUBSCRIPTION_ID=$(az account show --query id --output tsv) \
        AZURE_RESOURCE_GROUP=$RESOURCE_GROUP \
        AZURE_LOCATION=$LOCATION \
        PLATFORM_AUTH_TOKEN="azure-mesh-key-$(openssl rand -hex 8)" \
    --ports 8000 8443 8100 8101 8200 8201 8300 8301 8400 8401 8500 8501 \
    --file docker-compose.azure.yml

if [ $? -eq 0 ]; then
    echo_success "🎉 Deployment completed successfully!"
    
    # Get the FQDN
    FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_GROUP --query ipAddress.fqdn --output tsv)
    
    echo_success "📡 Platform deployed at: https://$FQDN:8443"
    echo_info "🔗 Platform endpoints:"
    echo "   • Platform API: https://$FQDN:8443"
    echo "   • Document Converter: https://$FQDN:8101"
    echo "   • Email Classifier: https://$FQDN:8201"
    echo "   • Email Parser: https://$FQDN:8301"
    echo "   • Image Classifier: https://$FQDN:8401"
    echo "   • Streaming Service: https://$FQDN:8501"
    
    echo_info "🧪 Testing deployment..."
    
    # Wait for deployment to be ready
    echo_info "Waiting for containers to be ready..."
    sleep 30
    
    # Test the main platform endpoint
    if curl -k -s "https://$FQDN:8443/health/live" > /dev/null; then
        echo_success "✅ Platform is responding correctly!"
    else
        echo_warning "⚠️  Platform may still be starting up. Check logs with:"
        echo "   az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_GROUP"
    fi
    
    echo_info "📊 View container logs:"
    echo "   az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_GROUP"
    
    echo_info "📈 Monitor container status:"
    echo "   az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_GROUP"
    
else
    echo_error "❌ Deployment failed. Check Azure portal for details."
    exit 1
fi

echo_success "🚀 Azure deployment script completed!"