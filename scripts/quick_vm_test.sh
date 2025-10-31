#!/usr/bin/env bash
set -euo pipefail

# Quick Azure VM Test - Single Command Execution
# Tests the production scripts without the full automation

echo "🚀 Quick Azure VM Test - Fixed Scripts"
echo

# Configuration - using different names to avoid conflicts
RESOURCE_GROUP="uv-conda-quick-test-rg" 
VM_NAME="uv-conda-quick-test-vm"
LOCATION="eastus"
VM_SIZE="Standard_D2s_v3"
IMAGE="Canonical:0001-com-ubuntu-server-jammy:22_04-lts-gen2:latest"
ADMIN_USERNAME="testuser"
SSH_KEY_PATH="$HOME/.ssh/id_rsa.pub"

echo "Creating Azure VM: $VM_NAME"

# Create resource group
az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output table

# Create VM
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
PUBLIC_IP=$(az vm show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$VM_NAME" \
    --show-details \
    --query publicIps \
    --output tsv)

echo "✅ VM created at: $PUBLIC_IP"

# Upload scripts
echo "📤 Uploading scripts..."
sleep 20  # Give VM time to fully boot

scp -o StrictHostKeyChecking=no \
    setup_hybrid_environment.sh \
    benchmark_hybrid.sh \
    $ADMIN_USERNAME@$PUBLIC_IP:~/

echo "✅ Scripts uploaded"
echo
echo "🔧 To test manually:"
echo "  ssh $ADMIN_USERNAME@$PUBLIC_IP"
echo "  ./setup_hybrid_environment.sh"
echo "  ./benchmark_hybrid.sh"
echo
echo "💰 To cleanup when done:"
echo "  az group delete --name $RESOURCE_GROUP --yes --no-wait"