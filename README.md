# Easy Local Chat LLM

🤖 **AIアシスタント搭載のローカルチャットシステム**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/ollama-required-orange.svg)](https://ollama.ai/)

WebSocketによるリアルタイム通信と、Ollama（Gemma3）を使ったローカルLLMボット機能を備えたチャットシステムです。研究用途に最適なデータ保存・エクスポート機能も搭載しています。

> このプロジェクトは [easy-local-chat](https://github.com/yamanori99/easy-local-chat) をベースに開発されています。

## ✨ 主な機能

### 💬 チャット機能
- リアルタイムチャット（WebSocket）
- 1対1チャット（ユーザー1人 + ボット）
- 自動再接続機能
- レスポンシブデザイン

### 🤖 AIボット機能
- ローカルLLM（Gemma3）による自動応答
- マンツーマンチャット対応
- 会話履歴の保持（最新100件、コンテキスト理解）
- 視覚的に区別しやすい専用UI

### 📊 研究用機能
- セッション・メッセージの自動保存
- タイムスタンプ付きデータディレクトリ管理
- 実験条件管理機能
- 実験条件のランダム割り当て
- 管理画面でのデータ可視化
- JSON/CSV形式でのエクスポート
- API経由でのデータ取得

## 必要条件

- **Python 3.9以上**（開発: 3.14.0）
- **Ollama**（LLMボット機能用）
- モダンブラウザ

**開発環境**: M4 Mac mini (16GB / 256GB) / macOS Tahoe 26.0.1

> ⚠️ macOS/Linuxでは仮想環境の使用を推奨します

## 📖 ドキュメント

- **[CHANGELOG.md](CHANGELOG.md)** - 変更履歴
- **[deployment/README.md](deployment/README.md)** - サーバー起動スクリプト
- **API**: `http://localhost:8000/docs` （起動後）

## 🚀 クイックスタート

### 1. Ollamaのセットアップ

> ⚠️ **重要**: Ollamaは**2つのコンポーネント**で構成されています
> 1. **Ollamaサービス**（本体） - 以下でインストール
> 2. **ollama Pythonパッケージ** - `pip install`で自動インストール

**OS別インストール:**

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# https://ollama.ai/ からインストーラーをダウンロード
```

**サービスを起動:**
```bash
ollama serve &
# 💡 別ターミナルで実行。バックグラウンドで動作し続けます
```

**モデルをダウンロード:**
```bash
ollama pull gemma3:4b
```

**利用可能なモデル:**

| モデル | サイズ | メモリ | 速度 | 精度 | 用途 |
|--------|--------|--------|------|------|------|
| `gemma3:1b` | 815MB | 4GB | ⚡⚡⚡ | ⭐⭐⭐ | 軽量・高速 |
| `gemma3:4b` | 3.3GB | 8GB | ⚡⚡ | ⭐⭐⭐⭐ | バランス型（デフォルト）🎯 |
| `gemma3:12b` | 8.1GB | 16GB | ⚡ | ⭐⭐⭐⭐⭐ | 高性能 |

### 2. プロジェクトのインストール
```bash
# リポジトリのクローン
git clone https://github.com/yamanori99/easy-local-chat.git
cd easy-local-chat

# 仮想環境のセットアップ
python3 -m venv venv

# 仮想環境の有効化
# macOS/Linux:
source venv/bin/activate
# Windows:
.\venv\Scripts\activate

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 3. サーバーの起動

```bash
# 起動スクリプトを使う（推奨）
./deployment/start_server_dev.sh

# または直接起動
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

初回起動時に管理者アカウント（ユーザー名とパスワード）を設定します。

### 4. 使用開始

1. ブラウザで `http://localhost:8000` にアクセス
   - 自動的に `http://localhost:8000/YYYYMMDD_HHMMSS/admin` にリダイレクトされます
2. **管理画面**で実験条件を作成
3. **ログイン画面**でユーザー名を入力
4. メッセージを送信すると、**ボットが自動応答**します！🤖

**テストメッセージ例:**
```
こんにちは！あなたは誰ですか？
```
```
Pythonでフィボナッチ数列を計算するコードを書いてください
```

## 📊 研究用データ保存

### データ構造
システム起動ごとにタイムスタンプ付きディレクトリが自動作成されます：

```
data/
└── 20241029_143022/         # 起動時刻のタイムスタンプ（再利用）
    ├── experiments/         # 実験グループ情報
    ├── conditions/          # 実験条件設定
    ├── sessions/            # セッション情報
    └── messages/            # メッセージデータ（ボット応答含む）
```

### 利用方法
- **管理画面**: `http://localhost:8000` → 自動リダイレクト
- **APIドキュメント**: `http://localhost:8000/docs`
- **データエクスポート**: 管理画面から JSON/CSV でダウンロード

### エクスポート手順
1. `http://localhost:8000` にアクセス（管理画面に自動リダイレクト）
2. セッションを選択
3. 「Export」ボタンをクリック
4. JSON/CSV形式で保存

### 実験条件管理機能
管理画面から実験条件を作成できます：

**基本設定:**
- ボットモデル（gemma3:1b, 4b, 12b など）
- システムプロンプト
- 自動セッション作成

**実験設定:**
- 実験条件名
- ランダム割り当て重み
- 条件ごとに異なるプロンプトやモデルを設定可能

**使用例（心理学実験）:**
```
テンプレートA: 条件A（共感的な応答）- 重み 1
テンプレートB: 条件B（中立的な応答）- 重み 1
テンプレートC: 統制群（最小限の応答）- 重み 1
→ ユーザーログイン時に自動的にいずれかの条件に割り当て
```

### ボットメッセージの識別

エクスポートされたデータでは、ボットメッセージは`message_type: "bot"`として記録されています：

```json
{
  "message_id": "msg_abc123",
  "session_id": "session_20251029_143052",
  "client_id": "bot",
  "message_type": "bot",
  "content": "こんにちは！私はAIアシスタントです。",
  "timestamp": "2025-10-29T14:30:52"
}
```

## ⚙️ カスタマイズ

### モデルの変更

`src/main.py`の43行目を編集：
```python
# 軽量モデル
bot_manager = BotManager(model="gemma3:1b", bot_client_id="bot")

# デフォルト（バランス型）
bot_manager = BotManager(model="gemma3:4b", bot_client_id="bot")

# 高性能モデル
bot_manager = BotManager(model="gemma3:12b", bot_client_id="bot")
```

### システムプロンプトの変更

`src/main.py`の`startup_event`関数内に追加：
```python
@app.on_event("startup")
async def startup_event():
    # カスタムプロンプトを設定
    bot_manager.set_system_prompt(
        "あなたは親切な日本語の先生です。日本語学習者の質問に丁寧に答えてください。"
    )
    # ... 既存のコード
```

### ボット名の変更

`src/static/js/chat.js`の272行目を編集：
```javascript
if (isBot) {
    clientIdSpan.textContent = '🧑‍🏫 日本語先生';  // カスタマイズ
    clientIdSpan.style.color = COLOR_PRESETS['bot'];
    clientIdSpan.style.fontWeight = 'bold';
}
```

### 管理者アカウントの変更

**初回起動時:**
- 対話式で設定
- または環境変数: `ADMIN_USERNAME`, `ADMIN_PASSWORD`

**変更方法:**
```bash
# data/admin_credentials.json を削除して再起動
rm data/admin_credentials.json
./deployment/start_server_dev.sh
```

## 🔧 トラブルシューティング

### ボットが応答しない

**確認事項:**
```bash
# 1. Ollamaサービスが起動しているか
ps aux | grep ollama

# 2. モデルがダウンロードされているか
ollama list

# 3. サーバーログを確認
# [BotManager] Error: ... のようなエラーがないか確認
```

### 応答が遅い

- より軽量なモデル（`gemma3:1b`）を使用
- システムリソースを確認（メモリ8GB以上推奨）
- 他のアプリケーションを終了

### モデルのダウンロードに失敗

```bash
# Ollamaサービスを再起動
killall ollama
ollama serve &

# モデルを再ダウンロード
ollama pull gemma3:4b
```

### 会話履歴がリセットされる

- セッションを終了すると会話履歴もクリアされます
- 同じセッション内では履歴が保持されます（最新100件まで）

### その他の問題

| 問題 | 解決方法 |
|------|---------|
| 接続エラー | ポート8000の使用状況を確認 |
| 仮想環境エラー | `python3 -m venv venv` で再作成 |
| pip エラー | `python3 -m pip install -r requirements.txt` を実行 |

## 🛠️ 技術スタック

- **Backend**: FastAPI, WebSocket, Ollama
- **Frontend**: HTML5, CSS3, JavaScript
- **LLM**: Gemma3 (Google)

```
src/
├── main.py              # メインサーバー
├── managers/
│   ├── bot_manager.py   # LLMボット管理
│   ├── session_manager.py
│   └── message_store.py
├── static/              # フロントエンド
└── templates/           # HTML
```

## 🔗 参考リンク

- [Ollama公式サイト](https://ollama.ai/)
- [Ollama モデルライブラリ](https://ollama.ai/library/gemma3)
- [元プロジェクト](https://github.com/yamanori99/easy-local-chat)
- [FastAPI ドキュメント](https://fastapi.tiangolo.com/)

## 💬 サポート

問題が解決しない場合は、GitHubのIssuesで報告してください。

## ライセンス

MIT License
