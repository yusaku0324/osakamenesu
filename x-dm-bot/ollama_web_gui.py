#!/usr/bin/env python3
"""
Ollama Web GUI - シンプルなチャットインターフェース
"""

from flask import Flask, render_template, request, jsonify, stream_with_context, Response
import subprocess
import json
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Qwen3 Chat GUI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f5f5f5;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .chat-container {
            flex: 1;
            max-width: 800px;
            width: 100%;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            background-color: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
        }
        
        .message {
            margin-bottom: 1rem;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            max-width: 70%;
            word-wrap: break-word;
        }
        
        .user-message {
            background-color: #3498db;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .ai-message {
            background-color: #ecf0f1;
            color: #2c3e50;
        }
        
        .input-area {
            padding: 1rem;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 0.5rem;
        }
        
        #messageInput {
            flex: 1;
            padding: 0.75rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        
        #sendButton {
            padding: 0.75rem 1.5rem;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        
        #sendButton:hover {
            background-color: #2980b9;
        }
        
        #sendButton:disabled {
            background-color: #95a5a6;
            cursor: not-allowed;
        }
        
        .typing-indicator {
            padding: 0.75rem 1rem;
            color: #7f8c8d;
            font-style: italic;
        }
        
        pre {
            background-color: #f4f4f4;
            padding: 0.5rem;
            border-radius: 4px;
            overflow-x: auto;
        }
        
        code {
            background-color: #f4f4f4;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Qwen3 Chat GUI</h1>
        <p>30Bパラメータの大規模言語モデル</p>
    </div>
    
    <div class="chat-container">
        <div class="messages" id="messages"></div>
        <div class="input-area">
            <input type="text" id="messageInput" placeholder="メッセージを入力..." autofocus>
            <button id="sendButton">送信</button>
        </div>
    </div>

    <script>
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        function addMessage(content, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
            messageDiv.innerHTML = content.replace(/\n/g, '<br>');
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function showTypingIndicator() {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'typing-indicator';
            typingDiv.id = 'typing';
            typingDiv.textContent = 'Qwen3が考えています...';
            messagesDiv.appendChild(typingDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function removeTypingIndicator() {
            const typingDiv = document.getElementById('typing');
            if (typingDiv) {
                typingDiv.remove();
            }
        }
        
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            messageInput.value = '';
            sendButton.disabled = true;
            
            showTypingIndicator();
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message }),
                });
                
                removeTypingIndicator();
                
                if (!response.ok) {
                    throw new Error('エラーが発生しました');
                }
                
                const data = await response.json();
                addMessage(data.response, false);
            } catch (error) {
                removeTypingIndicator();
                addMessage('エラー: ' + error.message, false);
            } finally {
                sendButton.disabled = false;
                messageInput.focus();
            }
        }
        
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'メッセージが空です'}), 400
        
        # Ollamaコマンドを実行
        cmd = ['ollama', 'run', 'qwen3:30b-a3b-q4_K_M', message]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return jsonify({'error': 'モデルの実行に失敗しました'}), 500
        
        return jsonify({'response': result.stdout.strip()})
        
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'タイムアウトしました'}), 504
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n🚀 Ollama Web GUI を起動しています...")
    print("📍 ブラウザで http://localhost:8080 を開いてください\n")
    app.run(host='0.0.0.0', port=8080, debug=False)