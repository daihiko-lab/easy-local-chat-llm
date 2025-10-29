# Easy Local Chat LLM

ローカルLLM bot機能を搭載したチャットシステム

## 元プロジェクト

このプロジェクトは [easy-local-chat](https://github.com/yamanori99/easy-local-chat) のフォークです。

## 追加機能

- 🤖 ローカルLLM botの統合
- （追加予定の機能をここに記載）

---
(以下の文章はフォーク先から）

# ローカルチャットシステム

シンプルで使いやすいローカルチャットシステムです。WebSocketを使用したリアルタイムコミュニケーションを実現します。

## 機能概要
- リアルタイムチャット機能
- 複数ユーザー同時接続対応
- 自動再接続機能
- レスポンシブデザイン
- システムメッセージ表示
- **📊 セッション・メッセージデータ保存機能（研究用）**
- **📈 管理画面でのデータ可視化・エクスポート**
- **💾 JSON/CSV形式でのデータエクスポート**

## 開発環境

M4 Mac mini (16GB / 256GB) / macOS Tahoe 26.0.1 / Python 3.14.0

## 必要条件
- Python 3.9以上（開発環境: 3.14.0）
- pip（Pythonパッケージマネージャー）
- モダンブラウザ（Chrome, Firefox, Safari, Edge等）

**重要**: macOSやLinuxの最新版では、システムPythonの保護により直接パッケージのインストールができない場合があります。必ず仮想環境を使用することを推奨します。

## クイックスタート

### 1. インストール
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

### 2. サーバーの起動

#### 方法1: 起動スクリプトを使う（推奨）

簡単に起動できるスクリプトを用意しています：

```bash
# サーバーを起動
./deployment/start_server.sh

# または、開発モード（自動リロード有効）
./deployment/start_server_dev.sh

# サーバーを停止
./deployment/stop_server.sh

# サーバーの状態確認
./deployment/server_status.sh
```

詳細は `deployment/README.md` を参照してください。

#### 方法2: 直接uvicornコマンドで起動

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

初回起動時に管理者パスワードの設定を求められます。

### 3. セッションの作成（初回必須）

**管理画面にアクセス**：
```
http://localhost:8000/admin
```

1. 設定した管理者パスワードでログイン
2. 「Create New Session」ボタンをクリック
3. セッションが作成されます

### 4. チャット画面へのアクセス

セッション作成後、参加者は以下のURLにアクセス：
```
http://localhost:8000
```

### 5. ネットワークアクセス
他のデバイスからアクセスする場合：

1. **IPアドレスの確認**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. **他のデバイスからのアクセス**
   ```
   http://[あなたのIPアドレス]:8000
   例: http://***.***.***.***:8000
   ```

3. **ファイアウォール設定**
   - macOS: システム環境設定 > セキュリティとプライバシー > ファイアウォール
   - Windows: Windows Defender ファイアウォール
   - Linux: ufw status でファイアウォール状態を確認

## 📊 データ保存機能（研究用）

### セッション管理
- **自動セッション作成**: サーバー起動時に自動的に新しいセッションが作成されます
- **セッションID**: タイムスタンプベースで一意のIDが生成されます（例: `session_20251029_143052`）
- **参加者追跡**: 各セッションで誰が参加したかを記録
- **メッセージカウント**: セッションごとの総メッセージ数を追跡

### データ保存
全てのメッセージは以下の情報とともに自動保存されます：
- メッセージID（一意）
- セッションID
- クライアントID（ユーザー名）
- メッセージタイプ（message/system）
- メッセージ内容
- タイムスタンプ
- メタデータ（文字数、単語数など）

### 管理画面（/admin）
管理画面では以下の操作が可能です：
- **現在のセッション情報表示**: アクティブなセッションの統計をリアルタイム表示
- **全セッション履歴**: 過去のセッション一覧を確認
- **データエクスポート**: JSON/CSV形式でデータをダウンロード
  - `messages.json`: 全メッセージデータ
  - `messages.csv`: CSV形式のメッセージ一覧
  - `session_summary.json`: セッションサマリー
- **セッション管理**: 新規セッション作成、セッション終了

### データ構造
```
data/
├── sessions/          # セッション情報
│   └── session_YYYYMMDD_HHMMSS.json
└── messages/          # メッセージデータ
    └── session_YYYYMMDD_HHMMSS.json

exports/              # エクスポートされたファイル
├── messages_session_xxx_YYYYMMDD_HHMMSS.csv
├── messages_session_xxx_YYYYMMDD_HHMMSS.json
└── session_summary_session_xxx_YYYYMMDD_HHMMSS.json
```

### API エンドポイント
研究用に以下のAPIエンドポイントを利用できます：
- `GET /api/sessions`: 全セッション取得
- `GET /api/sessions/{session_id}`: 特定のセッション情報
- `GET /api/sessions/{session_id}/messages`: セッションのメッセージ取得
- `GET /api/sessions/{session_id}/statistics`: セッション統計
- `GET /api/sessions/current/info`: 現在のセッション情報
- `POST /api/sessions/{session_id}/export?format=json|csv`: データエクスポート
- `POST /api/sessions/{session_id}/end`: セッション終了
- `POST /api/sessions/new`: 新規セッション作成

## 詳細な使用方法

### ログイン機能
- **ログイン方法**
  - 初回アクセス時にログイン画面が表示
  - クライアントIDを入力して入室
  - 一度入力したIDは自動的に保存（ブラウザセッション中）

- **ユーザー識別**
  - 各ユーザーに固有の色を自動割り当て
  - メッセージにユーザー名とカラーコードを表示
  - システムメッセージでユーザーの入退室を通知

- **セキュリティ**
  - クライアントIDの重複チェック
  - 不正なIDの入力防止（文字数制限、使用可能文字の制限）
  - WebSocket接続の認証確認

### チャット機能
- **メッセージ送信**
  - テキストボックスに入力
  - 送信ボタンまたはEnterキーで送信
- **メッセージ表示**
  - 自分のメッセージ：右側
  - 他のユーザーのメッセージ：左側
  - システムメッセージ：中央
  - すべてのメッセージにタイムスタンプ付き

### システム機能
- **自動再接続**
  - 接続が切れた場合に自動的に再接続
  - 接続状態をヘッダーに表示
- **マルチユーザー対応**
  - 複数ブラウザウィンドウでの同時接続可能
  - ユーザー参加/退出の通知

## セキュリティ設定

### クライアントID制限
- 最小文字数: 3文字
- 最大文字数: 20文字
- 使用可能文字: 英数字、アンダースコア(_)、ハイフン(-)
- 予約語の使用禁止（admin, system等）

### 接続制限
- 同一IPアドレスからの最大接続数: 5
- 接続タイムアウト: 60秒
- 再接続試行回数: 3回

### データ保護
- メッセージの一時保存のみ（永続化なし）
- クライアント情報の暗号化
- セッション管理によるセキュリティ確保

## 設定のカスタマイズ

### サーバー設定
```bash
# ポート番号の変更
uvicorn src.main:app --port 3000

# ホストの制限
uvicorn src.main:app --host 127.0.0.1

# SSL/TLS対応（開発環境）
uvicorn src.main:app --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem
```

### クライアント設定
- ブラウザのローカルストレージでユーザー設定を保存
- カスタムテーマの選択（ライト/ダーク）
- メッセージ表示設定のカスタマイズ

## トラブルシューティング

### 一般的な問題
1. **接続エラー**
   - ポート8000の使用状況を確認
   - ファイアウォール設定の確認
   - `netstat -ano | grep 8000` でポート状態確認

2. **表示の問題**
   - ブラウザのキャッシュをクリア
   - JavaScript有効化の確認
   - 開発者ツール（F12）でエラーを確認

3. **仮想環境関連の問題**
   - **externally-managed-environment エラー**
     ```bash
     # エラーメッセージが表示された場合は仮想環境を使用
     python3 -m venv venv
     source venv/bin/activate  # macOS/Linux
     .\venv\Scripts\activate   # Windows
     pip install -r requirements.txt
     ```
   
   - **pip コマンドが見つからない場合**
     ```bash
     python3 -m pip install -r requirements.txt
     ```

4. **ネットワークアクセスの問題**
   - 他のデバイスからアクセスできない場合：
     - 同じWiFi/LANネットワークに接続されているか確認
     - ルーターのゲスト接続分離設定を確認
     - IPアドレスが正しいか確認
     - ポート8000がブロックされていないか確認

## 開発者向け情報

### プロジェクト構造
```
easy-local-chat/
├── README.md
├── requirements.txt
├── data/                    # データ保存ディレクトリ（自動生成）
│   ├── sessions/           # セッションデータ
│   └── messages/           # メッセージデータ
├── exports/                 # エクスポートファイル（自動生成）
└── src/
    ├── main.py             # サーバーサイドロジック
    ├── models/             # データモデル
    │   ├── session.py
    │   └── message.py
    ├── managers/           # データ管理
    │   ├── session_manager.py
    │   └── message_store.py
    ├── exporters/          # データエクスポート
    │   └── data_exporter.py
    ├── static/             # 静的ファイル
    │   ├── css/
    │   ├── js/
    │   └── images/
    └── templates/          # HTMLテンプレート
        ├── login.html
        ├── chat.html
        ├── admin.html
        ├── admin_login.html
        └── viewer.html
```

### 使用技術
- **バックエンド**
  - FastAPI (Pythonフレームワーク)
  - WebSocket (リアルタイム通信)
- **フロントエンド**
  - HTML5
  - CSS3
  - JavaScript (ES6+)
- **開発ツール**
  - uvicorn (ASGIサーバー)
  - Jinja2 (テンプレートエンジン)

### デバッグ方法
- **サーバーサイド**
  - uvicornログの監視
  - FastAPIのデバッグモード活用

- **クライアントサイド**
  - 開発者ツール（F12）の使用
  - WebSocket通信の監視
  - コンソールログの確認

## ライセンス

MIT License
