#!/bin/bash

# Claude Code - Anthropic API Client
# Full-featured command line interface for Claude

VERSION="2.0.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
CONFIG_DIR="$HOME/.config/claude-code"
CONFIG_FILE="$CONFIG_DIR/config"
HISTORY_FILE="$CONFIG_DIR/history"
CONVERSATION_DIR="$CONFIG_DIR/conversations"

# Default settings
DEFAULT_MODEL="claude-opus-4-20250514"
DEFAULT_MAX_TOKENS="4096"
DEFAULT_TEMPERATURE="0.7"

# Initialize configuration
init_config() {
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$CONVERSATION_DIR"
    touch "$HISTORY_FILE"
}

# Load configuration
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    fi
    
    # Set defaults if not configured
    CLAUDE_MODEL="${CLAUDE_MODEL:-$DEFAULT_MODEL}"
    MAX_TOKENS="${MAX_TOKENS:-$DEFAULT_MAX_TOKENS}"
    TEMPERATURE="${TEMPERATURE:-$DEFAULT_TEMPERATURE}"
}

# Check API key
check_api_key() {
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        echo -e "${RED}Error: ANTHROPIC_API_KEY not set${NC}"
        echo ""
        echo "Please set your API key using one of these methods:"
        echo "1. Run: claude-code configure"
        echo "2. Export: export ANTHROPIC_API_KEY=your-api-key"
        echo ""
        echo "Get your API key from: https://console.anthropic.com/api"
        exit 1
    fi
}

# Show help
show_help() {
    cat << EOF
${BLUE}Claude Code v$VERSION${NC}
Command-line interface for Anthropic's Claude API

${YELLOW}Usage:${NC}
  claude-code [command] [options]

${YELLOW}Commands:${NC}
  ask <question>      Ask a single question
  chat               Start interactive chat session
  file <path>        Analyze a file with Claude
  code <request>     Generate code based on request
  configure          Configure API settings
  models             List available models
  history            Show conversation history
  clear              Clear conversation history
  help               Show this help message
  version            Show version information

${YELLOW}Options:${NC}
  -m, --model        Model to use (default: $DEFAULT_MODEL)
  -t, --temperature  Temperature 0-1 (default: $DEFAULT_TEMPERATURE)
  -x, --max-tokens   Max tokens (default: $DEFAULT_MAX_TOKENS)
  -s, --system       System prompt
  -f, --format       Output format (text/json/markdown)

${YELLOW}Examples:${NC}
  claude-code ask "What is the capital of France?"
  claude-code code "Create a Python function to sort a list"
  claude-code file script.py -s "Review this code for bugs"
  claude-code chat -m claude-3-sonnet-20240229

${YELLOW}Configuration:${NC}
  Config file: $CONFIG_FILE
  History file: $HISTORY_FILE

For more information, visit: https://docs.anthropic.com
EOF
}

# Configure settings
configure() {
    echo -e "${BLUE}Claude Code Configuration${NC}"
    echo ""
    
    # API Key
    current_key="${ANTHROPIC_API_KEY:-not set}"
    echo -e "Current API Key: ${YELLOW}${current_key:0:10}...${NC}"
    read -p "Enter new API key (or press Enter to keep current): " new_key
    if [ -n "$new_key" ]; then
        ANTHROPIC_API_KEY="$new_key"
    fi
    
    # Model selection
    echo ""
    echo "Available models:"
    echo "1. claude-opus-4-20250514 (Claude 4 - Most powerful)"
    echo "2. claude-sonnet-4-20250514 (Claude 4 - Balanced)"
    echo "3. claude-3-opus-20240229 (Claude 3 - Previous opus)"
    echo "4. claude-3-sonnet-20240229 (Claude 3 - Balanced)"
    echo "5. claude-3-haiku-20240307 (Claude 3 - Fastest)"
    read -p "Select model (1-5, default: 1): " model_choice
    
    case "$model_choice" in
        2) CLAUDE_MODEL="claude-sonnet-4-20250514" ;;
        3) CLAUDE_MODEL="claude-3-opus-20240229" ;;
        4) CLAUDE_MODEL="claude-3-sonnet-20240229" ;;
        5) CLAUDE_MODEL="claude-3-haiku-20240307" ;;
        *) CLAUDE_MODEL="claude-opus-4-20250514" ;;
    esac
    
    # Other settings
    echo ""
    read -p "Max tokens (default: $DEFAULT_MAX_TOKENS): " new_max_tokens
    MAX_TOKENS="${new_max_tokens:-$DEFAULT_MAX_TOKENS}"
    
    read -p "Temperature 0-1 (default: $DEFAULT_TEMPERATURE): " new_temp
    TEMPERATURE="${new_temp:-$DEFAULT_TEMPERATURE}"
    
    # Save configuration
    cat > "$CONFIG_FILE" << EOF
# Claude Code Configuration
ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
CLAUDE_MODEL="$CLAUDE_MODEL"
MAX_TOKENS="$MAX_TOKENS"
TEMPERATURE="$TEMPERATURE"
EOF
    
    chmod 600 "$CONFIG_FILE"
    echo ""
    echo -e "${GREEN}Configuration saved successfully!${NC}"
}

# Call Claude API
call_claude_api() {
    local messages="$1"
    local system_prompt="${2:-}"
    
    # Build request body
    local request_body="{
        \"model\": \"$CLAUDE_MODEL\",
        \"max_tokens\": $MAX_TOKENS,
        \"temperature\": $TEMPERATURE,
        \"messages\": $messages"
    
    if [ -n "$system_prompt" ]; then
        request_body="$request_body,
        \"system\": \"$system_prompt\""
    fi
    
    request_body="$request_body
    }"
    
    # Make API call
    local response=$(curl -s -X POST \
        https://api.anthropic.com/v1/messages \
        -H "Content-Type: application/json" \
        -H "x-api-key: $ANTHROPIC_API_KEY" \
        -H "anthropic-version: 2023-06-01" \
        -d "$request_body")
    
    # Check for errors
    if echo "$response" | grep -q '"error"'; then
        local error_msg=$(echo "$response" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
        echo -e "${RED}API Error: $error_msg${NC}" >&2
        return 1
    fi
    
    # Extract content
    echo "$response" | grep -o '"text":"[^"]*"' | sed 's/"text":"//;s/"$//' | sed 's/\\n/\n/g' | sed 's/\\"/"/g'
}

# Ask a single question
ask_question() {
    local question="$1"
    local system_prompt="${2:-}"
    
    if [ -z "$question" ]; then
        echo -e "${RED}Error: Please provide a question${NC}"
        echo "Usage: claude-code ask \"your question\""
        exit 1
    fi
    
    check_api_key
    
    echo -e "${CYAN}Asking Claude...${NC}"
    echo ""
    
    # Build messages array
    local messages='[{"role": "user", "content": "'"$question"'"}]'
    
    # Call API
    local response=$(call_claude_api "$messages" "$system_prompt")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Claude:${NC} $response"
        
        # Save to history
        echo "$(date '+%Y-%m-%d %H:%M:%S') | ask | $question" >> "$HISTORY_FILE"
    fi
}

# Interactive chat mode
chat_mode() {
    check_api_key
    
    echo -e "${BLUE}Starting Claude Chat${NC}"
    echo -e "${YELLOW}Model: $CLAUDE_MODEL${NC}"
    echo "Type 'exit' or 'quit' to end the conversation"
    echo "Type 'clear' to start a new conversation"
    echo "Type 'save' to save the conversation"
    echo ""
    
    local conversation="[]"
    local turn_count=0
    
    while true; do
        # Prompt
        echo -ne "${GREEN}You:${NC} "
        read -r user_input
        
        # Handle commands
        case "$user_input" in
            exit|quit)
                echo "Goodbye!"
                break
                ;;
            clear)
                conversation="[]"
                turn_count=0
                echo -e "${YELLOW}Conversation cleared${NC}"
                continue
                ;;
            save)
                local filename="$CONVERSATION_DIR/chat_$(date +%Y%m%d_%H%M%S).json"
                echo "$conversation" > "$filename"
                echo -e "${GREEN}Conversation saved to: $filename${NC}"
                continue
                ;;
            "")
                continue
                ;;
        esac
        
        # Add user message to conversation
        if [ $turn_count -eq 0 ]; then
            conversation='[{"role": "user", "content": "'"$user_input"'"}]'
        else
            # Remove last ]
            conversation="${conversation%]}"
            conversation="$conversation,{\"role\": \"user\", \"content\": \"$user_input\"}]"
        fi
        
        echo -e "${CYAN}Claude is thinking...${NC}"
        
        # Call API
        local response=$(call_claude_api "$conversation")
        
        if [ $? -eq 0 ]; then
            echo -e "${BLUE}Claude:${NC} $response"
            echo ""
            
            # Add assistant message to conversation
            conversation="${conversation%]}"
            conversation="$conversation,{\"role\": \"assistant\", \"content\": \"$response\"}]"
            
            ((turn_count++))
            
            # Save to history
            echo "$(date '+%Y-%m-%d %H:%M:%S') | chat | $user_input" >> "$HISTORY_FILE"
        else
            echo -e "${RED}Failed to get response${NC}"
        fi
    done
}

# Analyze file
analyze_file() {
    local filepath="$1"
    local system_prompt="${2:-Please analyze this file and provide insights.}"
    
    if [ -z "$filepath" ]; then
        echo -e "${RED}Error: Please provide a file path${NC}"
        echo "Usage: claude-code file <path>"
        exit 1
    fi
    
    if [ ! -f "$filepath" ]; then
        echo -e "${RED}Error: File not found: $filepath${NC}"
        exit 1
    fi
    
    check_api_key
    
    # Read file content
    local content=$(cat "$filepath" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
    local filename=$(basename "$filepath")
    
    echo -e "${CYAN}Analyzing $filename...${NC}"
    echo ""
    
    # Build message
    local question="Here is the content of $filename:\n\n$content"
    local messages='[{"role": "user", "content": "'"$question"'"}]'
    
    # Call API
    local response=$(call_claude_api "$messages" "$system_prompt")
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Analysis:${NC}"
        echo "$response"
    fi
}

# Generate code
generate_code() {
    local request="$1"
    
    if [ -z "$request" ]; then
        echo -e "${RED}Error: Please provide a code request${NC}"
        echo "Usage: claude-code code \"description of what you want\""
        exit 1
    fi
    
    check_api_key
    
    local system_prompt="You are an expert programmer. Generate clean, well-commented code based on the user's request. Include error handling and best practices."
    
    ask_question "$request" "$system_prompt"
}

# List available models
list_models() {
    echo -e "${BLUE}Available Claude Models:${NC}"
    echo ""
    echo -e "${GREEN}Claude 4 Family (Latest):${NC}"
    echo "  • claude-opus-4-20250514    - Most powerful model for complex challenges"
    echo "  • claude-sonnet-4-20250514  - Balanced performance for general tasks"
    echo ""
    echo -e "${GREEN}Claude 3 Family:${NC}"
    echo "  • claude-3-opus-20240229    - Previous generation opus model"
    echo "  • claude-3-sonnet-20240229  - Balanced performance and speed"
    echo "  • claude-3-haiku-20240307   - Fastest model, good for simple tasks"
    echo ""
    echo -e "${YELLOW}Current model: $CLAUDE_MODEL${NC}"
