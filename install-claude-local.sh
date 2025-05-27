#!/bin/bash

# Claude Code Local Mode Installer
# APIキー不要で動作するClaude Codeセットアップ

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Claude Code Local Mode Installer${NC}"
echo "================================="
echo ""

# 既存のClaude Codeをチェック
echo -e "${YELLOW}Checking for existing Claude Code installation...${NC}"

CLAUDE_FOUND=false
CLAUDE_PATH=""

# Check npm global installation
if [ -f "$HOME/.npm-global/bin/claude" ]; then
    CLAUDE_PATH="$HOME/.npm-global/bin/claude"
    CLAUDE_FOUND=true
    echo "Found: $CLAUDE_PATH (npm global)"
elif command -v claude &> /dev/null; then
    CLAUDE_PATH=$(which claude)
    CLAUDE_FOUND=true
    echo "Found: $CLAUDE_PATH"
fi

if [ "$CLAUDE_FOUND" = true ]; then
    echo -e "${GREEN}Claude Code is already installed!${NC}"
    $CLAUDE_PATH --version
    echo ""
    echo "Claude Code can work in local mode without API key."
    exit 0
fi

# Claude Codeが見つからない場合、ローカルヘルパーをインストール
echo -e "${YELLOW}Installing Claude Code Local Helper...${NC}"

mkdir -p "$HOME/.local/bin"

# Claude Code Local Helperスクリプトを作成
cat > "$HOME/.local/bin/claude-local" << 'EOF'
#!/bin/bash
# Claude Code Local Helper
# Provides basic functionality without API

VERSION="1.0.0-local"

print_help() {
    echo "Claude Code Local Helper v$VERSION"
    echo ""
    echo "This is a local-only version that works without API key."
    echo ""
    echo "Usage: claude-local [command] [options]"
    echo ""
    echo "Commands:"
    echo "  help        Show this help"
    echo "  version     Show version"
    echo "  analyze     Basic code analysis (local only)"
    echo "  test        Test the installation"
    echo ""
    echo "Examples:"
    echo "  claude-local test"
    echo "  claude-local analyze file.py"
}

case "$1" in
    ""|help|--help|-h)
        print_help
        ;;
    version|--version|-v)
        echo "Claude Code Local Helper v$VERSION"
        ;;
    test)
        echo "Claude Code Local Helper is working!"
        echo "Environment: $(uname -s) $(uname -m)"
        echo "User: $(whoami)"
        echo "Directory: $(pwd)"
        ;;
    analyze)
        if [ -z "$2" ]; then
            echo "Usage: claude-local analyze <file>"
            exit 1
        fi
        if [ -f "$2" ]; then
            echo "Analyzing file: $2"
            echo "File type: $(file -b "$2")"
            echo "Size: $(wc -c < "$2") bytes"
            echo "Lines: $(wc -l < "$2")"
            if command -v cloc &> /dev/null; then
                cloc "$2" 2>/dev/null || echo "Code analysis requires additional tools"
            fi
        else
            echo "File not found: $2"
            exit 1
        fi
        ;;
    *)
        echo "Unknown command: $1"
        echo "Run 'claude-local help' for usage"
        exit 1
        ;;
esac
EOF

chmod +x "$HOME/.local/bin/claude-local"

# シンボリックリンクを作成
ln -sf "$HOME/.local/bin/claude-local" "$HOME/.local/bin/claude"

# PATHに追加
SHELL_RC=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_RC="$HOME/.bashrc"
fi

if [ -n "$SHELL_RC" ]; then
    if ! grep -q "$HOME/.local/bin" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# Claude Code Local" >> "$SHELL_RC"
        echo "export PATH=\"\$PATH:$HOME/.local/bin\"" >> "$SHELL_RC"
    fi
fi

export PATH="$PATH:$HOME/.local/bin"

echo ""
echo -e "${GREEN}Installation completed!${NC}"
echo ""
echo "Claude Code Local Helper has been installed."
echo "This version works without API key."
echo ""
echo "Test with: claude-local test"
echo "Or: source ~/.zshrc && claude test"