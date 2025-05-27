#!/bin/bash
# デフォルトポートは5001、引数で変更可能
PORT=${1:-5001}

echo "Starting X DM Bot Web GUI..."
echo "Open http://localhost:$PORT in your browser"
python web_gui.py --port $PORT