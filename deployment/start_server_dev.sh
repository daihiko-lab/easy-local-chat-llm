#!/bin/zsh
# 開発モードでサーバーを起動（自動リロード有効）

# プロジェクトのルートディレクトリに移動
cd "$(dirname "$0")/.."

echo "=========================================="
echo "Easy Local Chat - Development Mode"
echo "=========================================="
echo ""

# 仮想環境の確認
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "Starting development server (auto-reload enabled)..."
echo ""
echo "📝 Access URLs will be displayed after startup completes."
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# 開発サーバーを起動（自動リロード有効）
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

