# Easy Local Chat LLM

🤖 **AIアシスタント搭載のローカルチャットシステム**

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/ollama-required-orange.svg)](https://ollama.ai/)

WebSocketによるリアルタイム通信と、Ollama（e.g., Gemma3）を使ったローカルLLMボット機能を備えたチャットシステムです。研究用途に最適なデータ保存・エクスポート機能も搭載しています。

> このプロジェクトは [easy-local-chat](https://github.com/yamanori99/easy-local-chat) をベースに開発されています。

## ✨ 主な機能

- **リアルタイムチャット**: WebSocketによる低遅延通信
- **AIボット**: ローカルLLM（e.g., Gemma3）による自動応答、会話履歴保持
- **実験管理**: 複数の実験条件を作成・管理、ランダム割り当て
- **🆕 多段階実験フロー**: 同意書、事前質問紙、チャット、事後質問紙、デブリーフィングなど、任意のステップを組み合わせた実験デザインに対応
- **データ管理**: セッション・メッセージの自動保存、JSON/CSV形式でのエクスポート
- **管理画面**: データ可視化、リアルタイム統計、セッション監視

## 必要条件

- **Python 3.9以上**
- **Ollama**（LLMボット機能用）
- モダンブラウザ

> ⚠️ macOS/Linuxでは仮想環境の使用を推奨します

## 🚀 クイックスタート

### 1. Ollamaのセットアップ

**インストール:**

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: https://ollama.ai/ からダウンロード
```

**起動とモデルのダウンロード:**

```bash
# サービスを起動
ollama serve &

# モデルをダウンロード（デフォルト: gemma3:4b）
ollama pull gemma3:4b
```

**利用可能なモデル:**

| モデル | サイズ | メモリ | 特徴 |
|--------|--------|--------|------|
| `gemma3:1b` | 815MB | 4GB | 軽量・高速 |
| `gemma3:4b` | 3.3GB | 8GB | バランス型（推奨）|
| `gemma3:12b` | 8.1GB | 16GB | 高性能 |

### 2. プロジェクトのセットアップ

```bash
# リポジトリのクローン
git clone https://github.com/yamanori99/easy-local-chat.git
cd easy-local-chat

# 仮想環境のセットアップ
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\activate  # Windows

# 依存パッケージのインストール
pip install -r requirements.txt
```

### 3. サーバーの起動

```bash
# 起動スクリプト（推奨）
./deployment/start_server_dev.sh

# または直接起動
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

初回起動時に管理者アカウント（ユーザー名とパスワード）を設定します。

### 4. アクセス

**ローカル（同じコンピュータ）:**
- 管理画面: `http://localhost:8000/admin`
- 参加者ログイン: `http://localhost:8000/login`

**ネットワーク（他のデバイス）:**
- 管理画面: `http://YOUR_IP:8000/admin`
- 参加者ログイン: `http://YOUR_IP:8000/login`

（IPアドレスはサーバー起動時に表示されます）

## 📖 使い方

### 実験の基本ワークフロー

1. **管理画面にアクセス** → `http://localhost:8000/admin`

2. **新しい実験を作成**
   - 実験名、説明、研究者名を入力
   - 必要に応じて最大同時セッション数を設定

3. **実験条件を作成**
   - 実験詳細画面で「新しいテンプレートを作成」
   - 条件名、ボットモデル、システムプロンプトを設定
   - 複数の条件を作成可能（自動的に実験に追加されます）
   - オプション：タイムリミット、教示文、アンケートを設定

4. **実験を開始**
   - 「実験を開始」ボタンをクリック

5. **参加者URLを共有**
   - ログインURL（`http://YOUR_IP:8000/login`）を参加者に送信
   - 参加者は自動的にランダムな条件に割り当てられます

6. **データの収集**
   - 管理画面でリアルタイムに統計情報を確認
   - 「Export」ボタンでJSON/CSV形式でダウンロード
   - アンケート回答も自動的に保存されます

## 📊 データ構造

実験ごとに分かりやすい名前のディレクトリが作成されます：

```
data/
└── user_study_2024/         # 実験名から自動生成
    ├── experiments/         # 実験設定
    ├── conditions/          # 実験条件
    ├── sessions/            # セッション情報
    ├── messages/            # メッセージデータ
    └── exports/             # エクスポートデータ
```

**重要な動作:**
- アクティブな実験のディレクトリは自動的に再利用されます
- サーバー再起動後も設定とデータは保持されます
- ボットメッセージは `message_type: "bot"` として記録されます

## 📝 アンケート機能

実験終了時に参加者にアンケートを表示できます。心理尺度の測定などに最適です。

### サポートされる質問タイプ

1. **リッカート尺度** (`likert`)
   - 例：「全く当てはまらない（1）～ 非常に当てはまる（7）」
   - 設定項目：`scale_min`, `scale_max`, `scale_min_label`, `scale_max_label`

2. **自由記述** (`text`)
   - 例：「実験の感想を教えてください」
   - 設定項目：`max_length`（最大文字数）

3. **単一選択** (`single_choice`)
   - 例：「性別を選んでください」
   - 設定項目：`choices`（選択肢のリスト）

4. **複数選択** (`multiple_choice`)
   - 例：「該当するものを全て選んでください」
   - 設定項目：`choices`（選択肢のリスト）

### アンケートの設定例（JSON）

```json
{
  "survey_title": "実験後アンケート",
  "survey_description": "ご協力ありがとうございました。以下のアンケートにお答えください。",
  "survey_questions": [
    {
      "question_id": "q1",
      "question_text": "AIの応答は自然でしたか？",
      "question_type": "likert",
      "scale_min": 1,
      "scale_max": 7,
      "scale_min_label": "全く自然でない",
      "scale_max_label": "非常に自然",
      "required": true
    },
    {
      "question_id": "q2",
      "question_text": "実験の感想を教えてください",
      "question_type": "text",
      "max_length": 500,
      "required": false
    }
  ]
}
```

### アンケートデータのエクスポート

- **セッション単位**: `/api/sessions/{session_id}/export/survey?format=csv`
- **実験全体**: `/api/experiments/{experiment_id}/export/survey?format=csv`

アンケート回答は参加者ごとに自動保存され、CSV/JSON形式でエクスポート可能です。

## ⚙️ カスタマイズ

### ボットモデルの変更

実験条件作成時に指定するか、`src/main.py`を編集：

```python
bot_manager = BotManager(model="gemma3:4b", bot_client_id="bot")
```

### 管理者アカウントの変更

```bash
# 認証情報ファイルを削除して再起動
rm data/admin_credentials.json
./deployment/start_server_dev.sh
```

## 🔧 トラブルシューティング

| 問題 | 解決方法 |
|------|---------|
| ボットが応答しない | `ps aux \| grep ollama` でOllamaの起動確認<br>`ollama list` でモデル確認 |
| 応答が遅い | 軽量モデル（`gemma3:1b`）を使用<br>メモリ8GB以上推奨 |
| 接続エラー | ポート8000の使用状況を確認 |
| モデルのダウンロード失敗 | Ollamaを再起動: `killall ollama && ollama serve &` |

## 🛠️ 技術スタック

- **Backend**: FastAPI, WebSocket, Ollama
- **Frontend**: HTML5, CSS3, JavaScript
- **LLM**: Gemma3 (Google)

## 📖 ドキュメント

- [CHANGELOG.md](CHANGELOG.md) - 変更履歴
- [deployment/README.md](deployment/README.md) - デプロイメントガイド
- **[EXPERIMENT_FLOW_GUIDE.md](EXPERIMENT_FLOW_GUIDE.md)** - 🆕 多段階実験フローの使い方
- API: `http://localhost:8000/docs` （起動後）

## 🔗 参考リンク

- [Ollama公式サイト](https://ollama.ai/)
- [元プロジェクト](https://github.com/yamanori99/easy-local-chat)
- [FastAPI ドキュメント](https://fastapi.tiangolo.com/)

## ライセンス

MIT License
