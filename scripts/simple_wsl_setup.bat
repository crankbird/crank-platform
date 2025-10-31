@echo off
REM Simple WSL2 instance creation - minimal error checking
REM Run this from Command Prompt (as Administrator)

echo Creating fresh WSL2 instance for GPU testing...

set instanceName=ubuntu-gpu-test
set instancePath=%LOCALAPPDATA%\WSL\%instanceName%
set rootfsPath=%TEMP%\ubuntu-fresh.tar.gz
set downloadUrl=https://cloud-images.ubuntu.com/wsl/jammy/current/ubuntu-jammy-wsl-amd64-ubuntu22.04lts.rootfs.tar.gz

echo.
echo Current WSL instances:
wsl --list --verbose

echo.
echo Downloading Ubuntu rootfs to: %rootfsPath%
echo From: %downloadUrl%
echo.

REM Simple download with curl
curl -L -o "%rootfsPath%" "%downloadUrl%"

echo.
echo Download completed. File info:
dir "%rootfsPath%"

echo.
echo Creating instance directory: %instancePath%
if exist "%instancePath%" rmdir /s /q "%instancePath%"
mkdir "%instancePath%"

echo.
echo Importing as WSL instance: %instanceName%
wsl --import %instanceName% "%instancePath%" "%rootfsPath%"

echo.
echo Setting up basic user account...
wsl -d %instanceName% -- bash -c "apt update -qq && useradd -m -s /bin/bash testuser && echo 'testuser:testpass' | chpasswd && usermod -aG sudo testuser"

echo.
echo Testing GPU access...
wsl -d %instanceName% -- nvidia-smi

echo.
echo Cleaning up...
del "%rootfsPath%"

echo.
echo Done! Instance created: %instanceName%
echo Login with: wsl -d %instanceName% -u testuser
echo Password: testpass
echo.
wsl --list --verbose

pause