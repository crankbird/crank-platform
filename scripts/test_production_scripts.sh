#!/usr/bin/env bash
set -euo pipefail

# Azure VM Test Runner - Production Version
# Creates VM, deploys scripts, runs complete test suite

echo "🚀 Azure VM Test Runner - Production Version"
echo "This will create a VM, test the hybrid approach, and clean up"
echo

# Configuration
RESOURCE_GROUP="uv-conda-test-v2-rg"
VM_NAME="uv-conda-test-v2-vm"

# Step 1: Create VM and deploy scripts
echo "📦 Step 1: Creating Azure VM and deploying scripts..."
cd "$(dirname "$0")"

# Update VM creation script with new resource group
sed -i "s/uv-conda-test-rg/$RESOURCE_GROUP/g" create_azure_test_vm_cpu.sh
sed -i "s/uv-conda-test-vm/$VM_NAME/g" create_azure_test_vm_cpu.sh

# Create VM
./create_azure_test_vm_cpu.sh

# Get the public IP from the output
PUBLIC_IP=$(az vm show \
    --resource-group "$RESOURCE_GROUP" \
    --name "$VM_NAME" \
    --show-details \
    --query publicIps \
    --output tsv)

echo "✅ VM created at: $PUBLIC_IP"
echo

# Step 2: Wait for VM to be ready
echo "⏳ Step 2: Waiting for VM to be fully ready..."
sleep 30

# Test SSH connectivity
for i in {1..10}; do
    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 testuser@$PUBLIC_IP "echo 'VM is ready'" 2>/dev/null; then
        echo "✅ VM is accessible"
        break
    else
        echo "⏳ Waiting for VM... attempt $i/10"
        sleep 15
    fi
    
    if [ $i -eq 10 ]; then
        echo "❌ VM not accessible after 10 attempts"
        exit 1
    fi
done

echo

# Step 3: Run the installation test
echo "🔧 Step 3: Running hybrid installation test..."
ssh testuser@$PUBLIC_IP "
    echo '🚀 Starting hybrid installation test...'
    chmod +x setup_hybrid_environment.sh benchmark_hybrid.sh
    
    echo '📦 Running installation...'
    if ./setup_hybrid_environment.sh; then
        echo '✅ Installation completed successfully'
    else
        echo '❌ Installation failed'
        exit 1
    fi
    
    echo '🏃 Running benchmarks...'
    if ./benchmark_hybrid.sh; then
        echo '✅ Benchmarks completed successfully'
    else
        echo '❌ Benchmarks failed'
        exit 1
    fi
    
    echo '📋 Final environment check...'
    export PATH=\"\$HOME/miniconda3/bin:\$PATH\"
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate aiml-hybrid
    
    echo 'Environment files created:'
    ls -la *.yml *.txt 2>/dev/null || echo 'No environment files found'
    
    echo '✅ Test completed successfully!'
"

if [ $? -eq 0 ]; then
    echo "🎉 All tests passed successfully!"
else
    echo "❌ Tests failed"
    exit 1
fi

echo

# Step 4: Cleanup
echo "🧹 Step 4: Cleaning up Azure resources..."
az group delete --name "$RESOURCE_GROUP" --yes --no-wait

echo "✅ Cleanup initiated (running in background)"
echo
echo "🎯 Summary:"
echo "  ✅ VM created and configured"
echo "  ✅ Hybrid installation successful"
echo "  ✅ Performance benchmarks completed"
echo "  ✅ No errors or manual interventions required"
echo "  ✅ Azure resources cleaned up"
echo
echo "🚀 Production-ready scripts validated!"