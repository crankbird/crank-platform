# PowerShell script to create a new WSL2 instance for GPU testing
# Run this from Windows PowerShell (as Administrator)

Write-Host "🐧 Setting up new WSL2 instance for GPU testing..." -ForegroundColor Green

# Check if WSL is installed
if (!(Get-Command wsl -ErrorAction SilentlyContinue)) {
    Write-Host "❌ WSL not found. Please install WSL2 first." -ForegroundColor Red
    exit 1
}

# List available distributions
Write-Host "`n📋 Available distributions:" -ForegroundColor Blue
wsl --list --online

# Create new WSL2 instance with Ubuntu 24.04
$instanceName = "ubuntu-gpu-test"
Write-Host "`n🚀 Creating new WSL2 instance: $instanceName" -ForegroundColor Yellow

try {
    # Install Ubuntu 24.04 LTS
    wsl --install -d Ubuntu-24.04 --name $instanceName
    
    Write-Host "✅ WSL2 instance created successfully!" -ForegroundColor Green
    Write-Host "`n📝 Next steps:" -ForegroundColor Blue
    Write-Host "1. Set up the new instance:"
    Write-Host "   wsl -d $instanceName"
    Write-Host ""
    Write-Host "2. In the new WSL instance, run these commands:"
    Write-Host "   sudo apt update && sudo apt upgrade -y"
    Write-Host "   sudo apt install -y curl git build-essential"
    Write-Host ""
    Write-Host "3. Copy the GPU setup script:"
    Write-Host "   # From your main WSL instance, copy the script to the new one"
    Write-Host ""
    Write-Host "4. Enable SSH for testing (optional):"
    Write-Host "   sudo apt install -y openssh-server"
    Write-Host "   sudo systemctl enable ssh"
    Write-Host "   sudo systemctl start ssh"
    Write-Host ""
    Write-Host "🎮 The new instance will have access to your NVIDIA GPU automatically!"
    
} catch {
    Write-Host "❌ Failed to create WSL2 instance: $_" -ForegroundColor Red
    
    # Alternative approach using wsl --import
    Write-Host "`n🔄 Trying alternative method..." -ForegroundColor Yellow
    
    # Download Ubuntu 24.04 rootfs if not exists
    $rootfsUrl = "https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-amd64-wsl.rootfs.tar.gz"
    $rootfsPath = "$env:TEMP\ubuntu-24.04-wsl.tar.gz"
    $instancePath = "$env:LOCALAPPDATA\WSL\$instanceName"
    
    if (!(Test-Path $rootfsPath)) {
        Write-Host "📥 Downloading Ubuntu 24.04 rootfs..." -ForegroundColor Blue
        Invoke-WebRequest -Uri $rootfsUrl -OutFile $rootfsPath
    }
    
    # Create instance directory
    New-Item -ItemType Directory -Path $instancePath -Force
    
    # Import the distribution
    wsl --import $instanceName $instancePath $rootfsPath
    
    Write-Host "✅ WSL2 instance imported successfully!" -ForegroundColor Green
}

Write-Host "`n🌐 Network Information:" -ForegroundColor Cyan
Write-Host "Both WSL instances will be on the same virtual network."
Write-Host "You can find IP addresses with: wsl hostname -I"
Write-Host ""
Write-Host "To access the new instance from your main WSL:"
Write-Host "1. Get the new instance IP: wsl -d $instanceName hostname -I"
Write-Host "2. SSH to it: ssh username@<ip_address>"