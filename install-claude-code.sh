#!/bin/bash

# Claude Code Installer - Simplified Version

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Claude Code Installer v1.0"
echo "=========================="
echo ""

# Create directories
echo "Creating directories..."
mkdir -p "$HOME/.claude-code"
mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.config/claude-code"

# Create Claude Code script
echo "Creating Claude Code script..."
cat > "$HOME/.claude-code/claude-code" << 'EOF'
#!/bin/bash

VERSION="1.0.0-demo"

case "$1" in
    ""|help|--help|-h)
        echo "Claude Code v$VERSION"
        echo ""
        echo "Usage: claude-code [command]"
        echo ""
        echo "Commands:"
        echo "  help        Show this help"
        echo "  version     Show version"
        echo "  configure   Set API key"
        echo "  ask         Ask a question"
        ;;
    version|--version|-v)
        echo "Claude Code v$VERSION"
        ;;
    configure)
        echo "Claude Code Configuration"
        read -p "Enter your Anthropic API key: " api_key
        if [ -n "$api_key" ]; then
            echo "ANTHROPIC_API_KEY=$api_key" > "$HOME/.config/claude-code/config"
            chmod 600 "$HOME/.config/claude-code/config"
            echo "API key saved!"
        fi
        ;;
    ask)
        if [ -z "$2" ]; then
            echo "Usage: claude-code ask \"your question\""
            exit 1
        fi
        echo "Question: $2"
        echo "(Demo mode - would send to Anthropic API)"
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run 'claude-code help' for usage"
        exit 1
        ;;
esac
EOF

# Make executable
chmod +x "$HOME/.claude-code/claude-code"

# Create symlink
ln -sf "$HOME/.claude-code/claude-code" "$HOME/.local/bin/claude-code"

# Add to PATH
SHELL_RC=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "$HOME/.local/bin" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# Claude Code" >> "$SHELL_RC"
        echo "export PATH=\"\$PATH:$HOME/.local/bin\"" >> "$SHELL_RC"
    fi
fi

echo ""
echo -e "${GREEN}Installation completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Run: source ~/.zshrc  (or source ~/.bashrc)"
echo "2. Test: claude-code help"
echo "3. Configure: claude-code configure"
echo ""
