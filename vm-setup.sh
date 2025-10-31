#!/bin/bash
set -e

echo "🚀 Setting up Crank Platform Development Environment"
echo "=============================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential development tools
echo "🔧 Installing development tools..."
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    nano \
    htop \
    tree \
    jq \
    unzip \
    build-essential \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common

# Install Docker
echo "🐳 Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# Install Docker Compose
echo "🐳 Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Node.js (LTS)
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python 3.12 and uv
echo "🐍 Installing Python and uv..."
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Azure CLI
echo "☁️ Installing Azure CLI..."
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install GitHub CLI
echo "🐱 Installing GitHub CLI..."
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh -y

# Install Graphite CLI
echo "📊 Installing Graphite CLI..."
npm install -g @withgraphite/graphite-cli@latest

# Set up development directories
echo "📁 Creating development directories..."
mkdir -p ~/projects
cd ~/projects

# Configure Git (user will need to set their own details)
echo "⚙️ Git configuration needed:"
echo "Please run these commands with your details:"
echo "git config --global user.name 'Your Name'"
echo "git config --global user.email 'your.email@example.com'"

# Set up SSH for GitHub (user will need to add their key)
echo "🔑 SSH key setup needed:"
echo "To set up GitHub access:"
echo "1. Generate SSH key: ssh-keygen -t ed25519 -C 'your.email@example.com'"
echo "2. Add to GitHub: cat ~/.ssh/id_ed25519.pub"
echo "3. Test connection: ssh -T git@github.com"

# Create useful aliases
echo "⚡ Setting up aliases..."
cat >> ~/.bashrc << 'EOF'

# Crank Platform Development Aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias projects='cd ~/projects'
alias crank='cd ~/projects/crank-platform'
alias doc='cd ~/projects/crankdoc'
alias email='cd ~/projects/parse-email-archive'
alias dps='docker ps'
alias dlog='docker logs'
alias dcup='docker-compose up'
alias dcdown='docker-compose down'
alias k='kubectl'

# Git aliases
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git pull'
alias gco='git checkout'
alias gb='git branch'

export EDITOR=nano
export PATH="$HOME/.local/bin:$PATH"
EOF

# Source the updated bashrc
source ~/.bashrc

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. SSH into the VM: ssh johnr@68.218.57.117"
echo "2. Configure Git with your details"
echo "3. Set up SSH key for GitHub"
echo "4. Clone your repositories"
echo "5. Connect VS Code Remote"
echo ""
echo "📝 VS Code Remote Setup:"
echo "1. Install 'Remote - SSH' extension in VS Code"
echo "2. Add SSH host: johnr@68.218.57.117"
echo "3. Connect and start coding!"
echo ""