#!/bin/bash

# Claude Code CLI Installer for Self-Hosted Runner
# This script installs Claude Code CLI on a GitHub Actions self-hosted runner

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Claude Code CLI Installer for Self-Hosted Runner${NC}"
echo "=================================================="
echo ""

# Check if running as appropriate user
echo "Running as user: $(whoami)"
echo "Home directory: $HOME"
echo ""

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.config/claude-code"

# Try to install Claude Code CLI using different methods

# Method 1: Check if already installed
if command -v claude-code &> /dev/null; then
    echo -e "${GREEN}Claude Code CLI is already installed!${NC}"
    claude-code --version
    exit 0
fi

# Method 2: Try npm installation (if npm is available)
if command -v npm &> /dev/null; then
    echo -e "${YELLOW}Attempting npm installation...${NC}"
    npm install -g @anthropic/claude-code 2>/dev/null || {
        echo -e "${YELLOW}npm installation failed, trying alternative methods...${NC}"
    }
fi

# Method 3: Download official binary (when available)
if ! command -v claude-code &> /dev/null; then
    echo -e "${YELLOW}Attempting to download official binary...${NC}"
    
    # Detect platform
    PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    # Map architecture names
    case "$ARCH" in
        x86_64) ARCH="amd64" ;;
        aarch64) ARCH="arm64" ;;
        armv7l) ARCH="arm" ;;
    esac
    
    echo "Platform: $PLATFORM"
    echo "Architecture: $ARCH"
    
    # Try to download from GitHub releases
    LATEST_RELEASE_URL="https://api.github.com/repos/anthropics/claude-code/releases/latest"
    
    # Get latest release info
    if command -v curl &> /dev/null; then
        RELEASE_INFO=$(curl -s "$LATEST_RELEASE_URL" 2>/dev/null || echo "{}")
        
        # Try to find appropriate asset
        DOWNLOAD_URL=$(echo "$RELEASE_INFO" | grep -o "https://[^\"]*claude-code[^\"]*${PLATFORM}[^\"]*${ARCH}[^\"]*" | head -1)
        
        if [ -n "$DOWNLOAD_URL" ]; then
            echo "Downloading from: $DOWNLOAD_URL"
            curl -L "$DOWNLOAD_URL" -o "$HOME/.local/bin/claude-code"
            chmod +x "$HOME/.local/bin/claude-code"
        fi
    fi
fi

# Method 4: Create a wrapper script that uses the API directly
if ! command -v claude-code &> /dev/null; then
    echo -e "${YELLOW}Creating Claude Code wrapper script...${NC}"
    
    cat > "$HOME/.local/bin/claude-code" << 'EOF'
#!/bin/bash
# Claude Code CLI Wrapper
# This wrapper provides basic Claude API functionality

VERSION="1.0.0-wrapper"

# Function to call Claude API
call_claude_api() {
    local message="$1"
    local api_key="${ANTHROPIC_API_KEY}"
    
    if [ -z "$api_key" ]; then
        echo "Error: ANTHROPIC_API_KEY environment variable not set"
        exit 1
    fi
    
    # Call Claude API
    response=$(curl -s -X POST \
        -H "x-api-key: $api_key" \
        -H "anthropic-version: 2023-06-01" \
        -H "content-type: application/json" \
        https://api.anthropic.com/v1/messages \
        -d "{
            \"model\": \"claude-3-haiku-20240307\",
            \"max_tokens\": 1000,
            \"messages\": [{\"role\": \"user\", \"content\": \"$message\"}]
        }" 2>/dev/null)
    
    # Extract the response text
    if [ $? -eq 0 ]; then
        echo "$response" | grep -o '"text":"[^"]*' | sed 's/"text":"//' | sed 's/\\n/\n/g' | sed 's/\\"/"/g'
    else
        echo "Error: Failed to call Claude API"
        exit 1
    fi
}

# Main command handling
case "$1" in
    --version|-v)
        echo "Claude Code CLI Wrapper v$VERSION"
        ;;
    --help|-h|help)
        echo "Claude Code CLI Wrapper v$VERSION"
        echo ""
        echo "Usage: claude-code [command] [options]"
        echo ""
        echo "Commands:"
        echo "  chat --message <msg>  Send a message to Claude"
        echo "  ask <question>        Ask Claude a question"
        echo "  --version            Show version"
        echo "  --help               Show this help"
        ;;
    chat)
        if [ "$2" = "--message" ] && [ -n "$3" ]; then
            call_claude_api "$3"
        else
            echo "Usage: claude-code chat --message <message>"
            exit 1
        fi
        ;;
    ask)
        if [ -n "$2" ]; then
            shift
            call_claude_api "$*"
        else
            echo "Usage: claude-code ask <question>"
            exit 1
        fi
        ;;
    "")
        # Read from stdin
        if [ -t 0 ]; then
            echo "Error: No input provided"
            echo "Usage: echo 'question' | claude-code"
            exit 1
        else
            input=$(cat)
            call_claude_api "$input"
        fi
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run 'claude-code --help' for usage"
        exit 1
        ;;
esac
EOF
    
    chmod +x "$HOME/.local/bin/claude-code"
fi

# Add to PATH in profile files
echo -e "${YELLOW}Updating PATH...${NC}"

add_to_path() {
    local profile_file="$1"
    if [ -f "$profile_file" ]; then
        if ! grep -q "$HOME/.local/bin" "$profile_file"; then
            echo "" >> "$profile_file"
            echo "# Claude Code CLI" >> "$profile_file"
            echo "export PATH=\"\$PATH:$HOME/.local/bin\"" >> "$profile_file"
            echo "Updated $profile_file"
        fi
    fi
}

# Update various shell profiles
add_to_path "$HOME/.bashrc"
add_to_path "$HOME/.bash_profile"
add_to_path "$HOME/.zshrc"
add_to_path "$HOME/.profile"

# Also update current session
export PATH="$PATH:$HOME/.local/bin"

# Verify installation
echo ""
echo -e "${YELLOW}Verifying installation...${NC}"

if command -v claude-code &> /dev/null; then
    echo -e "${GREEN}Claude Code CLI installed successfully!${NC}"
    echo ""
    claude-code --version
    echo ""
    echo -e "${GREEN}Installation complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Set the ANTHROPIC_API_KEY environment variable in your runner"
    echo "2. Test with: claude-code ask 'Hello, Claude!'"
else
    echo -e "${RED}Installation verification failed${NC}"
    echo "Please check the installation manually"
    exit 1
fi