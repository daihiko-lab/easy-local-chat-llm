# Easy Local Chat LLM

ローカルLLMを使った心理学実験用チャットシステム

## 特徴

- リアルタイムAIチャット（Ollama + WebSocket）
- 実験管理（条件分岐、ランダム割り当て）
- データエクスポート（JSON/CSV）
- 管理画面（統計表示、セッション監視）

## 必要要件

- Python 3.9+
- Ollama
- 8GB以上のRAM推奨

## セットアップ

### 1. Ollamaのインストール

```bash
# macOS
brew install ollama

# サービス起動
ollama serve &

# モデルダウンロード（例: qwen3:14b）
ollama pull qwen3:14b
```

### 2. プロジェクトのセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/your-repo/easy-local-chat-llm.git
cd easy-local-chat-llm

# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. サーバー起動

```bash
# 開発サーバー起動
./deployment/start_server_dev.sh

# または直接起動
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

初回起動時に管理者アカウントが設定されます。

## 使い方

### 基本的な実験の流れ

1. **管理画面にアクセス**: `http://localhost:8000/admin`

2. **実験を作成**
   - 実験名、説明、研究者名を入力
   - 「フローを編集」で実験の流れを設計

3. **実験フローの設計**
   - 同意説明、質問紙、チャット、分岐などのブロックを追加
   - チャットステップでAIモデルとプロンプトを設定
   - 条件分岐でランダム割り当てを設定

4. **実験を開始**
   - 「実験を開始」ボタンをクリック

5. **参加者URLを共有**
   - `http://YOUR_IP:8000/start/実験スラッグ` を参加者に送信
   - 参加者は自動的に条件に割り当てられる

6. **データ収集**
   - 管理画面でリアルタイム統計を確認
   - 「エクスポート」ボタンでCSV/JSON形式でダウンロード

## データ構造

```
data/
└── experiments/
    └── 実験スラッグ/
        ├── experiment.json      # 実験設定
        ├── sessions/            # セッション情報
        ├── messages/            # メッセージログ
        └── exports/             # エクスポートデータ
```

## M4 Mac最適化

チャットステップで以下のパラメータを設定可能：
- `num_thread`: CPUスレッド数（デフォルト: 8）
- `num_ctx`: コンテキスト長（デフォルト: 8192）
- `num_gpu`: GPUレイヤー数（デフォルト: -1、全レイヤー）
- `num_batch`: バッチサイズ（デフォルト: 512）

## モニタリング

### Ollamaのリアルタイム監視

別ターミナルで以下を実行すると、Ollamaの状態を1秒ごとに更新表示できます：

```bash
# watchコマンドのインストール（初回のみ）
brew install watch

# リアルタイム監視開始
watch -n 1 ollama ps
```

**表示される情報:**
- `NAME`: 実行中のモデル名
- `SIZE`: メモリ使用量
- `PROCESSOR`: CPU/GPU使用状況
- `CONTEXT`: コンテキストサイズ
- `UNTIL`: メモリから解放されるまでの時間

**停止方法:** `Ctrl+C`

### サーバーログの確認

サーバーログには各AI呼び出しの詳細が自動表示されます：

```
======================================================================
🤖 OLLAMA MODEL INVOCATION (STREAMING)
======================================================================
Session ID    : abc123...
Model         : qwen3:14b
System Prompt : You are an empathetic counselor...

Parameters:
  temperature      : 0.8
  top_p            : 0.9
  top_k            : 40
  repeat_penalty   : 1.1
  num_predict      : Default (unlimited)
  num_thread       : 8
  num_ctx          : 8192
  num_gpu          : -1 (all layers)
  num_batch        : 512

Conversation History: 3 messages
======================================================================

✅ Streaming response completed: 156 chars
```

これにより、各セッションでどのモデルがどんなパラメータで呼び出されているかを完全に把握できます。

## トラブルシューティング

| 問題 | 解決方法 |
|------|----------|
| Botが応答しない | `ollama serve` が起動しているか確認<br>`ollama list` でモデルを確認 |
| 応答が遅い | より小さいモデルを使用（例: gemma3:4b） |
| ポート8000が使用中 | `lsof -i:8000` でプロセスを確認して終了 |

## 技術スタック

- Backend: FastAPI, WebSocket, Ollama
- Frontend: HTML5, CSS3, JavaScript
- LLM: Ollama経由（Qwen, Gemma等）

## ドキュメント

- API仕様: `http://localhost:8000/docs`（起動後）
- [CHANGELOG.md](CHANGELOG.md) - バージョン履歴

## ライセンス

MIT License
