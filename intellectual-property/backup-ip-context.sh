#!/bin/bash

# Secure IP Context Backup Script
# Creates encrypted backup of GitHub Copilot context and IP development work
# 
# Usage: ./backup-ip-context.sh [--for-git]
# Output: Encrypted backup in ~/secure-backups/ or intellectual-property/encrypted-backups/

set -e

# Check for git integration flag
GIT_MODE=false
if [[ "$1" == "--for-git" ]]; then
    GIT_MODE=true
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    BACKUP_DIR="$SCRIPT_DIR/encrypted-backups"
else
    BACKUP_DIR="$HOME/secure-backups"
fi
DATE=$(date +%Y%m%d-%H%M)
BACKUP_NAME="ip-context-$DATE"
TEMP_DIR="/tmp/$BACKUP_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔒 Starting secure IP context backup...${NC}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$TEMP_DIR"

# Function to check if directory exists before backing up
backup_if_exists() {
    local source="$1"
    local dest="$2"
    
    if [ -d "$source" ]; then
        echo "  ✅ Backing up: $source"
        cp -r "$source" "$dest/"
    else
        echo "  ⚠️  Skipping (not found): $source"
    fi
}

echo -e "${YELLOW}📁 Collecting IP development context...${NC}"

# Backup GitHub Copilot conversation context
echo "🤖 GitHub Copilot Context:"
backup_if_exists "$HOME/.vscode-server/data/User/workspaceStorage" "$TEMP_DIR"
backup_if_exists "$HOME/.vscode-server/data/User/globalStorage/github.copilot-chat" "$TEMP_DIR"

# Backup crank-platform IP documentation (local working copies)
echo "📋 IP Documentation:"
backup_if_exists "$HOME/projects/crank-platform/intellectual-property" "$TEMP_DIR"

# Backup any local patent working files
echo "📝 Patent Working Files:"
backup_if_exists "$HOME/projects/crank-platform/patent-drafts-working" "$TEMP_DIR"

# Create manifest of what was backed up
echo "Creating backup manifest..."
cat > "$TEMP_DIR/BACKUP_MANIFEST.txt" << EOF
IP Context Backup - $DATE
================================

Backup Contents:
- GitHub Copilot conversation context
- VS Code workspace storage
- Crank Platform IP documentation
- Patent working files (if present)

⚠️  SECURITY WARNING:
This backup contains sensitive intellectual property information including:
- Complete patent development discussions
- Technical innovation details
- Competitive analysis and strategy
- Commercial validation data

KEEP THIS BACKUP SECURE AND ENCRYPTED!

Backup created: $(date)
Machine: $(hostname)
User: $(whoami)
WSL Distribution: $(cat /etc/os-release | grep PRETTY_NAME)
EOF

# Create tar archive
echo -e "${YELLOW}📦 Creating archive...${NC}"
cd /tmp
tar -czf "$BACKUP_NAME.tar.gz" "$BACKUP_NAME/"

# Check if GPG is available for encryption
if command -v gpg &> /dev/null; then
    echo -e "${YELLOW}🔐 Encrypting backup...${NC}"
    
    if [[ "$GIT_MODE" == true ]]; then
        # For git mode, use consistent naming and prompt for password
        echo -e "${YELLOW}📝 Git mode: Creating encrypted backup for repository storage${NC}"
        echo -e "${YELLOW}💡 Use a strong password that you'll remember - you'll need it to restore context${NC}"
        gpg --symmetric --cipher-algo AES256 --compress-algo 2 --output "$BACKUP_DIR/context-$DATE.gpg" "$BACKUP_NAME.tar.gz"
    else
        # Regular mode with more complex filename
        gpg --symmetric --cipher-algo AES256 --compress-algo 2 --output "$BACKUP_DIR/$BACKUP_NAME.tar.gz.gpg" "$BACKUP_NAME.tar.gz"
    fi
    
    # Remove unencrypted version
    rm "$BACKUP_NAME.tar.gz"
    
    if [[ "$GIT_MODE" == true ]]; then
        echo -e "${GREEN}✅ Encrypted backup created: $BACKUP_DIR/context-$DATE.gpg${NC}"
        echo -e "${GREEN}🔒 This file is safe to commit to git repository${NC}"
        
        # Show backup size
        BACKUP_SIZE=$(du -h "$BACKUP_DIR/context-$DATE.gpg" | cut -f1)
        echo -e "📊 Backup size: $BACKUP_SIZE"
        
        # Git integration suggestions
        echo -e "${YELLOW}📋 Suggested git commands:${NC}"
        echo "    git add intellectual-property/encrypted-backups/context-$DATE.gpg"
        echo "    git commit -m \"Encrypted context backup - $DATE\""
        echo "    git push"
        
    else
        echo -e "${GREEN}✅ Encrypted backup created: $BACKUP_DIR/$BACKUP_NAME.tar.gz.gpg${NC}"
        
        # Show backup size
        BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz.gpg" | cut -f1)
        echo -e "📊 Backup size: $BACKUP_SIZE"
    fi
    
else
    # No GPG available, warn user
    mv "$BACKUP_NAME.tar.gz" "$BACKUP_DIR/"
    echo -e "${RED}⚠️  WARNING: GPG not available, backup is NOT encrypted!${NC}"
    
    if [[ "$GIT_MODE" == true ]]; then
        echo -e "${RED}❌ CANNOT use --for-git mode without encryption!${NC}"
        echo -e "${RED}📁 Unencrypted backup: $BACKUP_DIR/$BACKUP_NAME.tar.gz${NC}"
        echo -e "${RED}🚫 DO NOT commit this to git - install GPG first!${NC}"
    else
        echo -e "${RED}📁 Unencrypted backup: $BACKUP_DIR/$BACKUP_NAME.tar.gz${NC}"
        echo -e "${RED}🔒 Please encrypt this file manually before storing!${NC}"
    fi
fi

# Cleanup temp directory
rm -rf "$TEMP_DIR"

echo -e "${GREEN}🎉 Backup complete!${NC}"
echo ""
echo -e "${YELLOW}📋 IMPORTANT SECURITY REMINDERS:${NC}"

if [[ "$GIT_MODE" == true ]]; then
    echo -e "${GREEN}✅ Encrypted backup is safe for git repository${NC}"
    echo -e "${GREEN}✅ Store decryption password securely (NOT in git)${NC}"
    echo -e "${GREEN}✅ Test decryption periodically to ensure backup validity${NC}"
    echo -e "${YELLOW}💡 Password is needed to restore context on new machines${NC}"
else
    echo -e "${RED}❌ NEVER commit this backup to git${NC}"
    echo -e "${RED}❌ NEVER upload to cloud storage without client-side encryption${NC}"
    echo -e "${RED}❌ NEVER share without explicit authorization${NC}"
    echo -e "${GREEN}✅ Store on encrypted external drive${NC}"
    echo -e "${GREEN}✅ Keep in secure physical location${NC}"
    echo -e "${GREEN}✅ Test restore procedure periodically${NC}"
fi

echo ""
if [[ "$GIT_MODE" == true ]]; then
    echo "🔄 To restore this backup on a new machine:"
    echo "1. Clone the repository"
    echo "2. Decrypt: gpg --decrypt context-$DATE.gpg > context-$DATE.tar.gz"
    echo "3. Extract: tar -xzf context-$DATE.tar.gz"
    echo "4. Follow context-restoration-guide.md instructions"
else
    echo "🔄 To restore this backup on a new machine:"
    echo "1. Install WSL and VS Code"
    echo "2. Decrypt: gpg --decrypt $BACKUP_NAME.tar.gz.gpg > $BACKUP_NAME.tar.gz"
    echo "3. Extract: tar -xzf $BACKUP_NAME.tar.gz"
    echo "4. Copy contents to appropriate locations"
fi