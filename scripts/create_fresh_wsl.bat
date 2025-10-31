@echo off
REM Batch script to create fresh WSL2 instance for GPU testing
REM Run this from Command Prompt (as Administrator)

echo Creating FRESH WSL2 instance for GPU testing...
echo This will be a completely clean Ubuntu installation

set instanceName=ubuntu-gpu-test
set instancePath=%LOCALAPPDATA%\WSL\%instanceName%

echo.
echo Checking current WSL instances:
wsl --list --verbose

echo.
echo Downloading fresh Ubuntu rootfs...

REM Try to download Ubuntu 22.04 rootfs (correct filename)
set rootfsPath=%TEMP%\ubuntu-fresh.tar.gz
set downloadUrl=https://cloud-images.ubuntu.com/wsl/jammy/current/ubuntu-jammy-wsl-amd64-ubuntu22.04lts.rootfs.tar.gz

echo Downloading from: %downloadUrl%
echo This may take a few minutes (325MB file)...

REM Delete any existing partial download
if exist "%rootfsPath%" del "%rootfsPath%"

REM Download with progress and better error handling
powershell -Command "& {$ProgressPreference = 'Continue'; try { Invoke-WebRequest -Uri '%downloadUrl%' -OutFile '%rootfsPath%' -UseBasicParsing } catch { Write-Host 'PowerShell download failed, trying curl...'; exit 1 }}"

if %errorlevel% neq 0 (
    echo PowerShell download failed, trying curl...
    curl -L --fail --show-error -o "%rootfsPath%" "%downloadUrl%"
)

REM Check if download was successful
if not exist "%rootfsPath%" (
    echo ERROR: Could not download Ubuntu rootfs
    echo Please download manually from:
    echo %downloadUrl%
    echo Save as: %rootfsPath%
    pause
    exit /b 1
)

REM Check file size - should be around 325MB
for %%I in ("%rootfsPath%") do set fileSize=%%~zI
if %fileSize% LSS 100000000 (
    echo ERROR: Download appears incomplete - file size: %fileSize% bytes
    echo Expected: ~325MB (341,000,000 bytes)
    echo Deleting partial download...
    del "%rootfsPath%"
    echo Please try again or download manually from:
    echo %downloadUrl%
    pause
    exit /b 1
)

echo Download successful - file size: %fileSize% bytes

echo.
echo Creating instance directory: %instancePath%
if exist "%instancePath%" rmdir /s /q "%instancePath%"
mkdir "%instancePath%"

echo.
echo Importing fresh Ubuntu as: %instanceName%
wsl --import %instanceName% "%instancePath%" "%rootfsPath%"

if %errorlevel% neq 0 (
    echo ERROR: Failed to import WSL instance
    pause
    exit /b 1
)

echo.
echo Setting up fresh instance...
wsl -d %instanceName% -- bash -c "apt update -qq && useradd -m -s /bin/bash testuser && echo 'testuser:testpass' | chpasswd && usermod -aG sudo testuser && apt install -y curl wget git build-essential && echo 'Fresh Ubuntu instance ready!' && lsb_release -a"

echo.
echo Testing GPU access...
wsl -d %instanceName% -- nvidia-smi --query-gpu=name --format=csv,noheader

echo.
echo Cleaning up download...
del "%rootfsPath%"

echo.
echo SUCCESS! Fresh WSL2 instance created: %instanceName%
echo.
echo Next steps:
echo 1. Start fresh instance: wsl -d %instanceName%
echo 2. Login as: testuser (password: testpass)
echo 3. Get IP: wsl -d %instanceName% -- hostname -I
echo 4. Copy GPU script from main instance
echo 5. Run GPU setup in clean environment
echo.
echo Updated WSL instances:
wsl --list --verbose

pause