# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-29

### Added
- 🤖 **ローカルLLM bot機能**（メジャー機能追加）
  - Ollamaとの統合によるAIアシスタント機能
  - マンツーマンチャット対応（ユーザーとボットの1対1会話）
  - **1ユーザー接続制限**（同時接続は1人のみ）
  - 会話履歴の保持（セッションごとに最新100件まで）
  - `BotManager`クラスの実装（`src/managers/bot_manager.py`）
  - ボット専用のメッセージタイプ（`bot`）
  - カスタマイズ可能なシステムプロンプト
  
- **UI/UX改善**
  - ボットメッセージ用の専用デザイン（緑色の背景）
  - ボットアイコンの視覚的識別（🤖 AI Assistant）
  - メッセージの改行を保持する表示機能
  
- **自動モデル管理**
  - サーバー起動時のOllamaモデル可用性チェック
  - モデルの自動ダウンロード機能

### Changed
- `requirements.txt` - `ollama==0.3.3`（Pythonクライアントライブラリ）を追加
- README.md - LLMボット機能の詳細な説明を追加
  - Ollamaのセットアップ手順
  - 利用可能なモデル一覧
  - トラブルシューティングガイド
  
### Technical Details
- 非同期処理によるボット応答生成
- ボットメッセージの永続化（研究用データとして保存）
- ストリーミング応答のサポート（将来の拡張用）

### Important Notes
- **Ollamaサービスの別途インストールが必須**
  - `ollama` Pythonパッケージは通信用クライアントライブラリ
  - Ollamaサービス本体は https://ollama.ai/ から別途インストール必要
  - 詳細は `SETUP_BOT.md` を参照

## [1.0.0] - 2025-10-29

### Added
- 初回リリース
- WebSocketベースのリアルタイムチャット機能
- セッション管理機能
- メッセージ保存機能（研究用）
- 管理画面（/admin）
- データエクスポート機能（JSON/CSV）
- パスワード保護機能
  - セッション全体のパスワード保護
  - ユーザーIDごとのパスワード保護
- レスポンシブデザイン
- 自動再接続機能
- `deployment/` ディレクトリ - ローカルサーバー起動用の便利なスクリプト集
  - `start_server.sh` - サーバーを起動（ネットワークアクセス可能）
  - `start_server_dev.sh` - 開発モードで起動（自動リロード有効）
  - `stop_server.sh` - サーバーを停止
  - `server_status.sh` - サーバーの状態を確認
  - `README.md` - deployment スクリプトの使い方ガイド

### Security
- .gitignore による機密情報の保護
  - data/ ディレクトリ（研究データ）を除外
  - exports/ ディレクトリを除外
  - 認証ファイル（.pem, .key, *credentials*）を除外

[1.0.0]: https://github.com/yamanori99/easy-local-chat/releases/tag/v1.0.0

