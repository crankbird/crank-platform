#!/usr/bin/env bash
set -euo pipefail

# Azure VM Setup for uv + conda Hybrid Testing (CPU-only)
# Creates a clean Ubuntu environment to validate the hybrid approach

# Configuration
RESOURCE_GROUP="uv-conda-test-rg"
VM_NAME="uv-conda-test-vm"
LOCATION="eastus"
VM_SIZE="Standard_D2s_v3"  # CPU-only for initial testing
IMAGE="Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest"
ADMIN_USERNAME="testuser"
SSH_KEY_PATH="$HOME/.ssh/id_rsa.pub"

echo "🚀 Setting up Azure VM for uv + conda hybrid testing (CPU-only)"
echo "Resource Group: $RESOURCE_GROUP"
echo "VM Name: $VM_NAME"
echo "Location: $LOCATION"
echo "VM Size: $VM_SIZE (CPU-only)"
echo

# Check if Azure CLI is installed
if ! command -v az >/dev/null 2>&1; then
    echo "❌ Azure CLI not found. Install with:"
    echo "   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    exit 1
fi

# Check if logged in
if ! az account show >/dev/null 2>&1; then
    echo "🔐 Logging into Azure..."
    az login
fi

# Create resource group
echo "📦 Creating resource group..."
az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION" \
    --output table

# Create VM (CPU-only)
echo "🖥️  Creating CPU-only VM..."
az vm create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$VM_NAME" \
    --image "$IMAGE" \
    --size "$VM_SIZE" \
    --admin-username "$ADMIN_USERNAME" \
    --ssh-key-values "$SSH_KEY_PATH" \
    --public-ip-sku Standard \
    --output table

# Get public IP
echo "🌐 Getting public IP address..."
PUBLIC_IP=$(az vm show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$VM_NAME" \
    --show-details \
    --query publicIps \
    --output tsv)

echo "✅ VM created successfully!"
echo
echo "Connection details:"
echo "  SSH: ssh $ADMIN_USERNAME@$PUBLIC_IP"
echo "  Public IP: $PUBLIC_IP"
echo
echo "Next steps:"
echo "1. SSH into the VM:"
echo "   ssh $ADMIN_USERNAME@$PUBLIC_IP"
echo
echo "2. Test the hybrid setup script (will be uploaded automatically)"
echo
echo "💰 Remember to delete the resource group when done:"
echo "   az group delete --name $RESOURCE_GROUP --yes --no-wait"

# Upload the test script to the VM
echo "📤 Uploading test scripts to VM..."

# Copy scripts with error handling
scp -o StrictHostKeyChecking=no -o ConnectTimeout=30 \
    setup_hybrid_environment.sh \
    benchmark_hybrid.sh \
    $ADMIN_USERNAME@$PUBLIC_IP:~/ || {
    echo "❌ Failed to upload scripts. VM may not be ready yet."
    echo "   Try manually after a few minutes:"
    echo "   scp setup_hybrid_environment.sh benchmark_hybrid.sh $ADMIN_USERNAME@$PUBLIC_IP:~/"
    exit 1
}

echo "✅ Scripts uploaded successfully:"
echo "  - setup_hybrid_environment.sh (main installation)"
echo "  - benchmark_hybrid.sh (performance testing)"
echo
echo "🚀 Ready to test! SSH in and run:"
echo "   ssh $ADMIN_USERNAME@$PUBLIC_IP"
echo "   ./setup_hybrid_environment.sh"
echo "   ./benchmark_hybrid.sh"