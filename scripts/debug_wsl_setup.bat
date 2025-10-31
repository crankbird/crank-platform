@echo off
REM Diagnostic WSL2 instance creation with detailed logging
REM Run this from Command Prompt (as Administrator)

echo Creating fresh WSL2 instance for GPU testing...
echo Logging all operations for debugging...

set instanceName=ubuntu-gpu-test
set instancePath=%LOCALAPPDATA%\WSL\%instanceName%
set rootfsPath=%TEMP%\ubuntu-fresh.tar.gz
set downloadUrl=https://cloud-images.ubuntu.com/wsl/jammy/current/ubuntu-jammy-wsl-amd64-ubuntu22.04lts.rootfs.tar.gz

echo.
echo === ENVIRONMENT INFO ===
echo Instance name: %instanceName%
echo Instance path: %instancePath%
echo Download path: %rootfsPath%
echo Download URL: %downloadUrl%
echo Temp directory: %TEMP%

echo.
echo === CURRENT WSL INSTANCES ===
wsl --list --verbose

echo.
echo === CLEANING UP ANY EXISTING FILES ===
if exist "%rootfsPath%" (
    echo Deleting existing file: %rootfsPath%
    del "%rootfsPath%"
    echo File deleted.
) else (
    echo No existing file to delete.
)

echo.
echo === TESTING CONNECTIVITY ===
echo Testing connection to Ubuntu cloud images...
curl -I --connect-timeout 10 https://cloud-images.ubuntu.com/wsl/jammy/current/
if %errorlevel% neq 0 (
    echo WARNING: Connection test failed
) else (
    echo Connection test successful
)

echo.
echo === DOWNLOADING UBUNTU ROOTFS ===
echo Starting download...
echo URL: %downloadUrl%
echo Target: %rootfsPath%
echo.

REM Try PowerShell first with detailed output
echo Attempting PowerShell download...
powershell -Command "& { try { $ProgressPreference = 'Continue'; Write-Host 'Starting PowerShell download...'; $response = Invoke-WebRequest -Uri '%downloadUrl%' -OutFile '%rootfsPath%' -UseBasicParsing -PassThru; Write-Host ('Downloaded ' + $response.Headers.'Content-Length' + ' bytes'); exit 0 } catch { Write-Host ('PowerShell error: ' + $_.Exception.Message); exit 1 } }"

if %errorlevel% neq 0 (
    echo PowerShell download failed, trying curl...
    echo.
    curl -v -L --fail --connect-timeout 30 --max-time 600 -o "%rootfsPath%" "%downloadUrl%"
    if %errorlevel% neq 0 (
        echo ERROR: Both PowerShell and curl failed
        echo Curl exit code: %errorlevel%
        pause
        exit /b 1
    )
)

echo.
echo === VERIFYING DOWNLOAD ===
if not exist "%rootfsPath%" (
    echo ERROR: File does not exist after download
    pause
    exit /b 1
)

for %%I in ("%rootfsPath%") do set fileSize=%%~zI
echo File exists: %rootfsPath%
echo File size: %fileSize% bytes

REM Check if it's a reasonable size (should be 300MB+)
if %fileSize% LSS 100000000 (
    echo WARNING: File size seems too small for Ubuntu rootfs
    echo Expected: ~325MB (341,000,000 bytes)
    echo Actual: %fileSize% bytes
    echo.
    echo File contents preview:
    powershell -Command "Get-Content '%rootfsPath%' -TotalCount 5 -Encoding Byte | ForEach-Object { [char]$_ }" 2>nul
    echo.
    echo This might be an error page or redirect. Continue anyway? (y/n)
    set /p continue=
    if /i not "%continue%"=="y" (
        echo Aborting...
        del "%rootfsPath%"
        pause
        exit /b 1
    )
)

echo Download verification complete.
echo.

echo === CREATING WSL INSTANCE ===
echo Creating instance directory: %instancePath%
if exist "%instancePath%" (
    echo Removing existing instance directory...
    rmdir /s /q "%instancePath%"
)
mkdir "%instancePath%"

echo Importing WSL instance: %instanceName%
wsl --import %instanceName% "%instancePath%" "%rootfsPath%"

if %errorlevel% neq 0 (
    echo ERROR: WSL import failed with exit code %errorlevel%
    echo This might indicate a corrupted download or WSL issue
    pause
    exit /b 1
)

echo WSL import successful!

echo.
echo === POST-IMPORT SETUP ===
echo Setting up basic environment...
wsl -d %instanceName% -- bash -c "apt update -qq && apt install -y sudo curl wget && useradd -m -s /bin/bash testuser && echo 'testuser:testpass' | chpasswd && usermod -aG sudo testuser && echo 'Setup complete'"

echo.
echo === GPU TEST ===
echo Testing GPU access...
wsl -d %instanceName% -- nvidia-smi --query-gpu=name --format=csv,noheader 2>nul
if %errorlevel% neq 0 (
    echo Note: nvidia-smi not available (expected on fresh install)
) else (
    echo GPU detected successfully!
)

echo.
echo === CLEANUP ===
echo Removing downloaded file...
del "%rootfsPath%"

echo.
echo === SUCCESS ===
echo Fresh WSL2 instance created: %instanceName%
echo Login: wsl -d %instanceName% -u testuser
echo Password: testpass
echo.
echo Updated WSL instances:
wsl --list --verbose

echo.
echo Ready for GPU hybrid script testing!
pause