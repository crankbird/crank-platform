# PowerShell script to safely create a named WSL2 instance for GPU testing
# Run this from Windows PowerShell (as Administrator)
# This will NOT affect your existing Ubuntu-22.04 instance

Write-Host "🐧 Creating FRESH WSL2 instance for GPU testing..." -ForegroundColor Green
Write-Host "🧹 This will be a completely clean Ubuntu installation" -ForegroundColor Yellow

$instanceName = "ubuntu-gpu-test"
$instancePath = "$env:LOCALAPPDATA\WSL\$instanceName"

Write-Host "`n📋 Checking current WSL instances:" -ForegroundColor Blue
wsl --list --verbose

# Download fresh Ubuntu rootfs for clean installation
Write-Host "`n� Downloading fresh Ubuntu rootfs for clean installation..." -ForegroundColor Cyan
    
    # Current official Ubuntu WSL rootfs URLs (these are the correct ones)
    $possibleUrls = @(
        "https://cloud-images.ubuntu.com/wsl/noble/current/ubuntu-noble-wsl-amd64-wsl.rootfs.tar.gz",
        "https://cloud-images.ubuntu.com/wsl/jammy/current/ubuntu-jammy-wsl-amd64-wsl.rootfs.tar.gz"
    )
    
    $rootfsPath = "$env:TEMP\ubuntu-wsl.tar.gz"
    $downloadSuccess = $false
    
    foreach ($url in $possibleUrls) {
        try {
            Write-Host "📥 Trying to download from: $url"
            Invoke-WebRequest -Uri $url -OutFile $rootfsPath -TimeoutSec 30
            if (Test-Path $rootfsPath -and (Get-Item $rootfsPath).Length -gt 100MB) {
                $downloadSuccess = $true
                break
            }
        } catch {
            Write-Host "❌ Failed to download from: $url" -ForegroundColor Yellow
        }
    }
    
    if ($downloadSuccess) {
        Write-Host "📁 Creating instance directory: $instancePath"
        if (Test-Path $instancePath) {
            Remove-Item -Path $instancePath -Recurse -Force
        }
        New-Item -ItemType Directory -Path $instancePath -Force
        
        Write-Host "📥 Importing rootfs as: $instanceName"
        wsl --import $instanceName $instancePath $rootfsPath
        
        Write-Host "✅ Successfully created $instanceName from fresh Ubuntu rootfs!" -ForegroundColor Green
        
        # Set up the fresh instance
        Write-Host "🔧 Setting up fresh instance..."
        wsl -d $instanceName -- bash -c "
            # Update package lists
            apt update -qq
            
            # Create a user account
            useradd -m -s /bin/bash testuser
            echo 'testuser:testpass' | chpasswd
            usermod -aG sudo testuser
            
            # Install essential packages
            apt install -y curl wget git build-essential
            
            echo 'Fresh Ubuntu instance ready!'
            lsb_release -a
        "
        
        # Test GPU access
        Write-Host "🎮 Testing GPU access in fresh instance..."
        wsl -d $instanceName -- nvidia-smi --query-gpu=name --format=csv,noheader
        
        # Cleanup downloaded file
        Remove-Item -Path $rootfsPath -Force
    } else {
        Write-Host "❌ Could not download Ubuntu rootfs automatically." -ForegroundColor Red
        Write-Host "`n📋 Manual download method:" -ForegroundColor Blue
        Write-Host "1. Download Ubuntu 24.04 WSL rootfs manually from:"
        Write-Host "   https://cloud-images.ubuntu.com/wsl/noble/current/"
        Write-Host "   File: ubuntu-noble-wsl-amd64-wsl.rootfs.tar.gz"
        Write-Host "2. Save it as: $env:TEMP\ubuntu-fresh.tar.gz"
        Write-Host "3. Run: wsl --import $instanceName $instancePath $env:TEMP\ubuntu-fresh.tar.gz"
        Write-Host ""
        Write-Host "OR try Ubuntu 22.04:"
        Write-Host "   https://cloud-images.ubuntu.com/wsl/jammy/current/"
        Write-Host "   File: ubuntu-jammy-wsl-amd64-wsl.rootfs.tar.gz"
        exit 1
    }
}

Write-Host "`n📋 Updated WSL instances:" -ForegroundColor Blue
wsl --list --verbose

Write-Host "`n🎮 GPU Testing Setup:" -ForegroundColor Green
Write-Host "1. Start your new instance:"
Write-Host "   wsl -d $instanceName"
Write-Host ""
Write-Host "2. Connect to fresh instance:"
Write-Host "   wsl -d $instanceName"
Write-Host "   # Login as: testuser (password: testpass)"
Write-Host ""
Write-Host "3. Get the fresh instance IP:"
Write-Host "   wsl -d $instanceName -- hostname -I"
Write-Host ""
Write-Host "4. Copy GPU script from your main instance:"
Write-Host "   # From Ubuntu-22.04: scp /path/to/gpu-script testuser@<fresh-ip>:~/"
Write-Host ""
Write-Host "5. Run the GPU setup script in the CLEAN environment"
Write-Host ""
Write-Host "🚀 Both instances will have GPU access and can communicate over WSL network!"

Write-Host "`n⚠️  Your original Ubuntu-22.04 instance is completely safe!" -ForegroundColor Yellow