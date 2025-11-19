from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Form, Cookie
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from typing import Dict, Optional
import json
import random
import os
import hashlib
import secrets
import uuid
import asyncio
import socket
from datetime import datetime
from pathlib import Path

from .models.session import Session, SurveyResponse
from .models.message import Message
from .models.condition import Condition, SurveyQuestion
from .models.experiment_group import ExperimentGroup
from .managers.session_manager import SessionManager
from .managers.message_store import MessageStore
from .exporters.data_exporter import DataExporter
from .managers.bot_manager import BotManager
from .managers.condition_manager import ConditionManager
from .managers.experiment_manager import ExperimentManager

def generate_random_color():
    return f'#{random.randint(0, 0xFFFFFF):06x}'

app = FastAPI()

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

# ヘルスチェック（デバッグ用）
@app.get("/api/health")
async def health_check():
    """HTTPリクエストが到達しているか確認するためのエンドポイント"""
    return {
        "status": "ok",
        "message": "Server is running",
        "timestamp": datetime.now().isoformat()
    }

# 接続中のクライアントを保持する辞書
# key: 接続ID（ユニーク）, value: WebSocket接続
active_connections: Dict[str, WebSocket] = {}
client_colors: Dict[str, str] = {} # クライアントIDと色の対応を保持
client_sessions: Dict[str, str] = {} # 接続IDとセッションIDの対応を保持
connection_to_display_name: Dict[str, str] = {} # 接続ID→表示名のマッピング
connection_to_base_name: Dict[str, str] = {} # 接続ID→ベース名のマッピング

# 実験管理のインスタンス（最初に初期化）
experiment_manager = ExperimentManager()

# データ管理のインスタンス（動的ディレクトリ参照）
# 実験がある場合は自動的にそのディレクトリを使用
base_data_dir = Path("data")

session_manager = SessionManager(
    data_dir=str(base_data_dir / "sessions"),
    experiment_manager=experiment_manager  # 動的ディレクトリ参照用
)
message_store = MessageStore(
    data_dir=str(base_data_dir / "messages"),
    experiment_manager=experiment_manager  # 動的ディレクトリ参照用
)
data_exporter = DataExporter()
condition_manager = ConditionManager(
    condition_file=str(base_data_dir / "conditions" / "conditions.json"),
    experiment_manager=experiment_manager  # 動的ディレクトリ参照用
)

# ボット管理のインスタンス（モデルは各セッション作成時に条件から設定）
bot_manager = BotManager(bot_client_id="bot")

# 管理者認証用
ADMIN_CREDENTIALS_FILE = "data/admin_credentials.json"
admin_tokens: Dict[str, bool] = {}  # トークン: 認証済みフラグ

# セッショントークン管理（ユニークなURL生成用）
# key: トークン, value: {"client_id": str, "condition_id": str, "created_at": str}
session_tokens: Dict[str, dict] = {}

def get_admin_credentials() -> Optional[dict]:
    """管理者認証情報を取得"""
    if os.path.exists(ADMIN_CREDENTIALS_FILE):
        with open(ADMIN_CREDENTIALS_FILE, 'r') as f:
            return json.load(f)
    return None

def set_admin_credentials(username: str, password: str):
    """管理者認証情報を設定"""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    Path(ADMIN_CREDENTIALS_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(ADMIN_CREDENTIALS_FILE, 'w') as f:
        json.dump({
            "username": username,
            "password_hash": password_hash
        }, f, ensure_ascii=False, indent=2)
    print(f"Admin credentials set successfully. Username: {username}")

def verify_admin_credentials(username: str, password: str) -> bool:
    """管理者認証情報を検証"""
    stored_creds = get_admin_credentials()
    if not stored_creds:
        return False
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return (stored_creds.get('username') == username and 
            stored_creds.get('password_hash') == password_hash)

def generate_admin_token() -> str:
    """管理者認証トークンを生成"""
    token = secrets.token_urlsafe(32)
    admin_tokens[token] = True
    return token

def verify_admin_token(token: Optional[str]) -> bool:
    """管理者トークンを検証"""
    if not token:
        print(f"[Auth] ❌ No token")
        return False
    
    is_valid = admin_tokens.get(token, False)
    print(f"[Auth] {'✅' if is_valid else '❌'} {token[:12]}")
    return is_valid

# アプリケーション起動時の処理
async def cleanup_empty_sessions():
    """空のセッション（参加者0）を定期的にクリーンアップ"""
    while True:
        await asyncio.sleep(60)  # 1分ごとにチェック
        
        try:
            sessions = session_manager.get_active_sessions()
            for session in sessions:
                # 作成から30秒以上経過 & 参加者が0
                idle_seconds = session.get_idle_seconds()
                if idle_seconds > 30 and len(session.participants) == 0:
                    print(f"[Cleanup] 🧹 Ending empty session: {session.session_id} (idle for {idle_seconds:.0f}s)")
                    session_manager.end_session(session.session_id)
                    
                    # ボット履歴もクリア
                    if session.session_id in bot_manager.conversation_history:
                        bot_manager.clear_history(session.session_id)
        except Exception as e:
            print(f"[Cleanup] Error during cleanup: {e}")

@app.on_event("startup")
async def startup_event():
    global session_manager, bot_manager, experiment_manager
    
    # 起動情報を表示
    print("\n" + "="*60)
    print("APPLICATION STARTUP")
    print("="*60)
    
    # アクティブな実験があればそのディレクトリを表示
    active_exp = experiment_manager.get_active_experiment()
    if active_exp:
        data_dir = Path(active_exp.data_directory)
        print(f"📁 Active Experiment Data Directory: {data_dir.name}")
        print(f"   ├─ Experiments: {data_dir / 'experiments'}")
        print(f"   ├─ Conditions: {data_dir / 'conditions'}")
        print(f"   ├─ Sessions: {data_dir / 'sessions'}")
        print(f"   └─ Messages: {data_dir / 'messages'}")
    else:
        print(f"📁 Base Data Directory: data/")
        print(f"   ⚠️  No active experiment. Please create one from /admin")
    print("="*60 + "\n")
    
    # Ollamaサービスの可用性をチェック
    print("\n" + "="*60)
    print("OLLAMA SERVICE CHECK")
    print("="*60)
    try:
        import ollama
        ollama_client = ollama
        models = ollama.list()
        available_models = [m['name'] for m in models.get('models', [])]
        if available_models:
            print(f"✓ Ollama is running with {len(available_models)} model(s) available:")
            for model_name in available_models[:5]:  # Show first 5 models
                print(f"  - {model_name}")
            if len(available_models) > 5:
                print(f"  ... and {len(available_models) - 5} more")
        else:
            print("✗ Warning: Ollama is running but no models are installed.")
            print("  Please pull at least one model (e.g., ollama pull gemma3:4b)")
    except Exception as e:
        print(f"✗ Warning: Could not connect to Ollama service.")
        print(f"  Error: {e}")
        print("  Please ensure Ollama is installed and running.")
        print("  Visit: https://ollama.ai/")
    print("="*60 + "\n")
    
    # 管理者認証情報のチェック
    stored_creds = get_admin_credentials()
    if not stored_creds:
        print("\n" + "="*60)
        print("ADMIN SETUP")
        print("="*60)
        print("管理者アカウントが設定されていません。")
        print("環境変数または対話式で設定してください。")
        print()
        
        # 環境変数から認証情報を取得
        env_username = os.environ.get('ADMIN_USERNAME', 'admin')
        env_password = os.environ.get('ADMIN_PASSWORD')
        
        if env_password:
            set_admin_credentials(env_username, env_password)
            print(f"Admin credentials set from environment. Username: {env_username}")
        else:
            # 標準入力から認証情報を取得
            import getpass
            print("対話式セットアップ：")
            username = input("管理者ユーザー名 [admin]: ").strip() or "admin"
            
            while True:
                password = getpass.getpass("管理者パスワード: ")
                if len(password) < 4:
                    print("パスワードは4文字以上である必要があります。")
                    continue
                confirm = getpass.getpass("パスワード確認: ")
                if password != confirm:
                    print("パスワードが一致しません。もう一度入力してください。")
                    continue
                set_admin_credentials(username, password)
                break
        print("="*60 + "\n")
    
    # 既存のアクティブなセッションをチェック
    active_sessions = session_manager.get_active_sessions()
    
    if active_sessions:
        print(f"Found {len(active_sessions)} active session(s):")
        for session in active_sessions:
            print(f"  - {session.session_id}")
    else:
        print("No active sessions found. Please create a session from the admin panel.")
    
    # アクセスURLを表示
    print("\n" + "="*60)
    print("🌐 ACCESS URLS")
    print("="*60)
    
    # ローカルIPアドレスを取得
    import socket
    local_ip = None
    try:
        # ダミー接続でローカルIPを取得（実際には接続しない）
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        # IPアドレス取得に失敗した場合
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = None
    
    # localhost URL
    print(f"📍 Local Access (this computer):")
    print(f"   Root:         http://localhost:8000/")
    print(f"   Admin Panel:  http://localhost:8000/admin")
    print(f"   User Login:   http://localhost:8000/login")
    
    # ネットワークIP URL
    if local_ip and local_ip != "127.0.0.1":
        print(f"\n📡 Network Access (other devices on same network):")
        print(f"   Root:         http://{local_ip}:8000/")
        print(f"   Admin Panel:  http://{local_ip}:8000/admin")
        print(f"   User Login:   http://{local_ip}:8000/login")
        print(f"\n💡 Share the Login Page URL with participants!")
    
    print("="*60 + "\n")
    
    # バックグラウンドタスクを起動
    asyncio.create_task(cleanup_empty_sessions())
    print("🧹 Background cleanup task started (checks every 60 seconds)\n")

@app.get("/")
async def get(request: Request):
    """ルートは常にログイン画面へリダイレクト"""
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login")
async def login_page(request: Request):
    """ログイン画面"""
    return templates.TemplateResponse("login.html", {
        "request": request
    })

def get_local_ip():
    """サーバーのローカルIPアドレスを取得"""
    try:
        # ダミーのUDP接続でローカルIPを取得
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

@app.get("/api/connection/status")
async def get_connection_status():
    """現在の接続状況を取得"""
    # アクティブな実験の存在をチェック
    active_exp = experiment_manager.get_active_experiment()
    
    if not active_exp:
        # アクティブな実験がない場合
        return JSONResponse(content={
            "is_available": False,
            "reason": "No active experiment available. Please contact the administrator."
        })
    
    # 実験がある場合は常にログイン可能
    return JSONResponse(content={
        "is_available": True,
        "reason": ""
    })

@app.get("/api/server/ip")
async def get_server_ip():
    """サーバーのIPアドレスを取得"""
    local_ip = get_local_ip()
    return JSONResponse(content={
        "local_ip": local_ip,
        "port": 8000
    })

@app.post("/api/login")
async def login(participant_code: str = Form(...), participant_password: str = Form(...)):
    """ログイン処理：参加者コードとパスワードを検証してセッショントークンを生成"""
    # アクティブな実験の存在をチェック
    active_exp = experiment_manager.get_active_experiment()
    if not active_exp:
        return JSONResponse(
            status_code=400,
            content={"error": "No active experiment available"}
        )
    
    # 🆕 参加者コードを検証
    participant_code = participant_code.lower().strip()
    participant_password = participant_password.lower().strip()
    
    if not active_exp.is_code_valid(participant_code):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid participant code"}
        )
    
    # 🆕 パスワードを検証
    if not active_exp.verify_code_password(participant_code, participant_password):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid password"}
        )
    
    code_status = active_exp.get_code_status(participant_code)
    
    if code_status == "completed":
        return JSONResponse(
            status_code=400,
            content={"error": "This experiment has already been completed with this code"}
        )
    
    if code_status == "used":
        # 🆕 使用中のコードはブロック（再接続禁止）
        return JSONResponse(
            status_code=400,
            content={"error": "This participant code has already been used. Please contact the researcher."}
        )
    
    # unused の場合のみ新規セッションを作成
    
    # client_idを生成（participant_codeベース）
    client_id = f"participant_{participant_code}"
    
    # ユニークなトークンを生成
    token = secrets.token_urlsafe(32)
    
    # トークン情報を保存（条件はフローで動的に決定される）
    session_tokens[token] = {
        "client_id": client_id,
        "participant_code": participant_code,
        "experiment_id": active_exp.experiment_id,
        "created_at": datetime.now().isoformat()
    }
    
    print(f"[Login] 🎫 Token generated for '{participant_code}':")
    print(f"   Token: {token[:16]}...")
    print(f"   Client ID: {client_id}")
    print(f"   Experiment: {active_exp.name}")
    
    return JSONResponse(content={
        "token": token,
        "client_id": client_id,
        "participant_code": participant_code
    })

@app.get("/viewer")
async def viewer(request: Request, session_id: str, admin_token: Optional[str] = Cookie(None)):
    """管理者用のセッションビューワー（読み取り専用）"""
    # 認証チェック
    if not verify_admin_token(admin_token):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # セッションが存在するか確認
    session = session_manager.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return templates.TemplateResponse("viewer.html", {
        "request": request,
        "session_id": session_id
    })

@app.get("/chat")
async def chat(request: Request, token: str):
    """チャット画面を表示（トークンベース）"""
    
    # トークンの検証
    if token not in session_tokens:
        print(f"[Chat] ❌ Invalid token")
        return RedirectResponse(url="/login", status_code=302)
    
    token_data = session_tokens[token]
    client_id = token_data["client_id"]
    participant_code = token_data.get("participant_code", "N/A")
    experiment_id = token_data.get("experiment_id")
    
    # アクティブな実験の存在をチェック
    active_exp = experiment_manager.get_active_experiment()
    if not active_exp:
        print(f"[Chat] No active experiment found")
        return RedirectResponse(url="/login", status_code=302)
    
    print(f"[Chat] 🎫 User accessing chat with token:")
    print(f"   Client ID: {client_id}")
    print(f"   Participant Code: {participant_code}")
    print(f"   Experiment: {active_exp.name}")
    print(f"   (Session will be created on WebSocket connection)")
    
    return templates.TemplateResponse("chat.html", {
        "request": request, 
        "token": token,
        "client_id": client_id,
        "session_id": None,  # 新規セッション（WebSocketで作成）
        "experiment": active_exp  # 実験情報を渡す
    })

@app.websocket("/ws/viewer")
async def websocket_viewer_endpoint(websocket: WebSocket, session_id: str):
    """管理者用の読み取り専用WebSocket接続"""
    await websocket.accept()
    
    # セッションが存在するか確認
    if session_id:
        session = session_manager.load_session(session_id)
        if not session:
            await websocket.close(code=1000, reason="Session not found")
            return
    else:
        await websocket.close(code=1000, reason="Session ID required")
        return
    
    # 管理者ID（特殊なID）
    viewer_id = f"admin_viewer_{id(websocket)}"
    active_connections[viewer_id] = websocket
    client_sessions[viewer_id] = session_id
    
    print(f"[Viewer] → {session_id}")
    
    try:
        # 管理者はメッセージを受信するだけ（送信しない）
        while True:
            # メッセージを受信し続けるが、何もしない
            data = await websocket.receive_json()
            # 管理者からのメッセージは無視
            pass
    except WebSocketDisconnect:
        if viewer_id in active_connections:
            del active_connections[viewer_id]
        if viewer_id in client_sessions:
            del client_sessions[viewer_id]
        print(f"[Viewer] ← {session_id}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocketエンドポイント（トークンベース認証）"""
    await websocket.accept()
    client_id = None
    session_id = None
    session_created_now = False
    
    try:
        while True:
            data = await websocket.receive_json()
            if not client_id:
                # 初期メッセージからトークンを取得して検証
                token = data.get("token")
                if not token or token not in session_tokens:
                    print(f"[WebSocket] ❌ Invalid or missing token")
                    await websocket.close(code=1000, reason="Invalid token")
                    return
                
                # トークンから情報を取得
                token_data = session_tokens[token]
                base_client_id = token_data["client_id"]
                participant_code = token_data.get("participant_code")
                experiment_id = token_data.get("experiment_id")
                
                print(f"[WS] 🎫 {base_client_id} | Code: {participant_code or 'None'} | Exp: {experiment_id}")
                
                # アクティブな実験の存在をチェック
                active_exp = experiment_manager.get_active_experiment()
                if not active_exp:
                    await websocket.close(code=1000, reason="No active experiment")
                    return
                
                # セッション作成（フローベース）
                # session_idを生成（client_idベース + タイムスタンプ）
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                session_id = f"sess_{timestamp}"
                session = session_manager.create_session(session_id=session_id)
                
                # セッション情報を設定
                session.client_id = base_client_id
                session.experiment_id = active_exp.experiment_id  # ✅ 実験IDを設定
                session_manager.update_session(session)
                session_created_now = True
                
                # 🆕 参加者コードをセッションに保存
                if participant_code:
                    session.participant_code = participant_code
                    session_manager.update_session(session)
                    
                    # 実験に参加者コードを "used" としてマーク
                    active_exp.mark_code_used(participant_code, base_client_id, session_id)
                    from pathlib import Path
                    experiment_manager._save_experiment(active_exp, Path(active_exp.data_directory))
                    print(f"[Code] {participant_code} → used")
                
                # トークンを使用済みにする（1回のみ使用可能）
                del session_tokens[token]
                print(f"[Token] Consumed")
                
                # フローベースのシステムでは、ボット設定はチャットステップで適用される
                print(f"[Session] {session_id} | Exp: {active_exp.name}")
                
                # 背後でユニークな接続IDを生成（UUID使用）
                # 既存のIDと衝突しないことを保証
                while True:
                    connection_id = uuid.uuid4().hex
                    if connection_id not in active_connections:
                        break
                
                # 表示名は元のクライアントIDをそのまま使用（番号を付けない）
                display_name = base_client_id
                
                client_id = connection_id  # 内部的にはユニークな接続IDを使用
                connection_to_display_name[connection_id] = display_name
                connection_to_base_name[connection_id] = base_client_id
                
                print(f"[Connect] {display_name}")
                
                active_connections[client_id] = websocket
                client_sessions[client_id] = session_id  # セッションIDを記録
                
                # セッションに参加者を追加（表示名を使用）
                session_manager.add_participant(session_id, display_name)
                
                # 実験の統計を再計算（セッション数と参加者数）
                session = session_manager.get_session(session_id)
                if session and session.experiment_id:
                    experiment_manager.recalculate_experiment_statistics(session.experiment_id, session_manager)
                
                # 新規セッション作成の場合、session_idをクライアントに送信
                if session_created_now:
                    session_info = {
                        "type": "session_created",
                        "session_id": session_id,
                        "message": f"Session {session_id} created successfully"
                    }
                    await websocket.send_json(session_info)
                
                # システムメッセージを作成・保存
                join_message = Message(
                    session_id=session_id,
                    client_id=display_name,
                    internal_id=client_id,  # 内部UUID（分析用）
                    message_type="system",
                    content=f"Client {display_name} has joined the room",
                    timestamp=data["timestamp"]
                )
                message_store.save_message(join_message)
                
                message = {
                    "type": "system",
                    "client_id": display_name,
                    "internal_id": client_id,  # 内部UUID（色生成用）
                    "message": f"Client {display_name} has joined the room",
                    "timestamp": data["timestamp"]
                }
                await broadcast_message(message, target_session_id=session_id)
                
                # 🆕 フローシステムがすべてのステップを管理（教示文含む）
            elif data["type"] == "message":
                # 表示名を取得
                display_name = connection_to_display_name.get(client_id, client_id)
                
                # ユーザーメッセージを保存
                user_message = Message(
                    session_id=session_id,
                    client_id=display_name,
                    internal_id=client_id,  # 内部UUID（分析用）
                    message_type="message",
                    content=data["message"],
                    timestamp=data["timestamp"]
                )
                message_store.save_message(user_message)
                
                # セッションのメッセージ数をインクリメント
                session_manager.increment_message_count(session_id)
                
                message = {
                    "type": "message",
                    "client_id": display_name,
                    "internal_id": client_id,  # 内部UUID（色生成用）
                    "message": data["message"],
                    "timestamp": data["timestamp"],
                }
                await broadcast_message(message, target_session_id=session_id)
                
                # ボットが応答を生成（ボット自身のメッセージには反応しない）
                if not bot_manager.is_bot_message(client_id):
                    try:
                        # ボットの応答を生成
                        bot_response = await bot_manager.generate_response(
                            user_message=data["message"],
                            session_id=session_id,
                            client_id=client_id
                        )
                        
                        # ボットのメッセージを作成・保存
                        bot_message_obj = Message(
                            session_id=session_id,
                            client_id=bot_manager.bot_client_id,
                            internal_id="bot",  # ボット用の固定ID
                            message_type="bot",  # ボット専用のメッセージタイプ
                            content=bot_response,
                            timestamp=datetime.now().isoformat()
                        )
                        message_store.save_message(bot_message_obj)
                        
                        # セッションのメッセージ数をインクリメント
                        session_manager.increment_message_count(session_id)
                        
                        # ボットの応答をブロードキャスト
                        bot_broadcast = {
                            "type": "bot",
                            "client_id": bot_manager.bot_client_id,
                            "internal_id": "bot",  # ボットも固定ID（色生成用）
                            "message": bot_response,
                            "timestamp": bot_message_obj.timestamp,
                        }
                        await broadcast_message(bot_broadcast, target_session_id=session_id)
                        
                    except Exception as e:
                        print(f"Error generating bot response: {e}")
            elif data["type"] == "join":
                # 新規参加者の通知（既に上で処理済み）
                pass

    except WebSocketDisconnect:
        if client_id:
            # 表示名を取得
            display_name = connection_to_display_name.get(client_id, client_id)
            base_name = connection_to_base_name.get(client_id)
            
            if client_id in active_connections:
                del active_connections[client_id]
            if client_id in client_sessions:
                del client_sessions[client_id]
            if client_id in connection_to_display_name:
                del connection_to_display_name[client_id]
            if client_id in connection_to_base_name:
                del connection_to_base_name[client_id]
            
            print(f"[Disconnect] User '{display_name}' disconnected (connection_id: {client_id})")
            
            # セッションから参加者を削除（表示名を使用）
            session_manager.remove_participant(session_id, display_name)
            
            # 切断メッセージを保存
            leave_message = Message(
                session_id=session_id,
                client_id=display_name,
                internal_id=client_id,  # 内部UUID（分析用）
                message_type="system",
                content=f"Client {display_name} has left the room",
                timestamp=datetime.now().isoformat()
            )
            message_store.save_message(leave_message)
            
            message = {
                "type": "system",
                "client_id": display_name,
                "internal_id": client_id,  # 内部UUID（色生成用）
                "message": f"Client {display_name} has left the room",
                "timestamp": datetime.now().isoformat()
            }
            await broadcast_message(message, target_session_id=session_id)
            
            # セッションに参加者がいなくなったかチェック
            session = session_manager.load_session(session_id)
            if session and len(session.participants) == 0:
                # 全参加者が切断した場合
                print(f"[Session] All participants left session {session_id}")
                
                # ボットの会話履歴をクリア
                if session_id in bot_manager.conversation_history:
                    print(f"[Session] Clearing bot conversation history for {session_id}")
                    bot_manager.clear_history(session_id)
                
                # セッションを終了状態にする
                print(f"[Session] Ending session {session_id} (no participants)")
                session_manager.end_session(session_id)

async def broadcast_message(message: dict, target_session_id: str = None):
    """指定されたセッションの接続中のクライアントにメッセージをブロードキャストする
    
    Args:
        message: 送信するメッセージ
        target_session_id: 対象のセッションID。指定された場合、そのセッションの参加者のみに送信
    """
    for client_id, connection in active_connections.items():
        # セッションIDが指定されている場合、そのセッションに属するクライアントのみに送信
        if target_session_id:
            if client_sessions.get(client_id) == target_session_id:
                await connection.send_json(message)
        else:
            # セッションIDが指定されていない場合は全員に送信（後方互換性）
            await connection.send_json(message)

# ========== 管理API エンドポイント ==========

@app.get("/admin/login")
async def admin_login_page(request: Request):
    """管理者ログイン画面"""
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin/auth")
async def admin_authenticate(username: str = Form(...), password: str = Form(...)):
    """管理者認証"""
    if verify_admin_credentials(username, password):
        token = generate_admin_token()
        response = RedirectResponse(url="/admin", status_code=302)
        response.set_cookie(key="admin_token", value=token, httponly=True, max_age=86400)  # 24時間有効
        return response
    else:
        # 認証失敗
        return RedirectResponse(url="/admin/login?error=1", status_code=302)

@app.get("/admin/logout")
async def admin_logout():
    """管理者ログアウト"""
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie(key="admin_token")
    return response

@app.get("/admin")
async def admin_page(request: Request, admin_token: Optional[str] = Cookie(None)):
    """管理画面"""
    # 認証チェック
    if not verify_admin_token(admin_token):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/admin/experiment/{experiment_id}")
async def experiment_detail_page(request: Request, experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """実験詳細管理画面"""
    # 認証チェック
    if not verify_admin_token(admin_token):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # 実験を取得
    experiment = experiment_manager.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    return templates.TemplateResponse("experiment_detail.html", {
        "request": request,
        "experiment": experiment
    })

@app.get("/admin/experiment/{experiment_id}/flow")
async def experiment_flow_editor_page(request: Request, experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """実験フロー編集専用ページ"""
    # 認証チェック
    if not verify_admin_token(admin_token):
        return RedirectResponse(url="/admin/login", status_code=302)
    
    # 実験を取得
    experiment = experiment_manager.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # JSONシリアライズ
    import json
    experiment_json = json.dumps(experiment.to_dict())
    
    return templates.TemplateResponse("experiment_flow_editor.html", {
        "request": request,
        "experiment": experiment,
        "experiment_json": experiment_json
    })

@app.get("/api/sessions")
async def get_sessions():
    """全セッションの取得"""
    sessions = session_manager.get_all_sessions()
    return JSONResponse(content={
        "sessions": [s.to_dict() for s in sessions]
    })

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """特定のセッション情報を取得"""
    summary = session_manager.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    return JSONResponse(content=summary)

@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """セッションのメッセージを取得"""
    messages = message_store.get_messages_by_session(session_id)
    return JSONResponse(content={
        "messages": [m.to_dict() for m in messages]
    })

@app.get("/api/sessions/{session_id}/statistics")
async def get_session_statistics(session_id: str):
    """セッションの統計情報を取得"""
    stats = message_store.get_session_statistics(session_id)
    return JSONResponse(content=stats)

@app.get("/api/sessions/current/info")
async def get_current_session_info():
    """現在のセッション情報を取得"""
    current_session = session_manager.get_current_session()
    if not current_session:
        raise HTTPException(status_code=404, detail="No active session")
    
    summary = session_manager.get_session_summary(current_session.session_id)
    stats = message_store.get_session_statistics(current_session.session_id)
    
    return JSONResponse(content={
        "session": summary,
        "statistics": stats
    })

@app.post("/api/sessions/{session_id}/export")
async def export_session_data(session_id: str, format: str = "json"):
    """セッションデータをエクスポート（直接ダウンロード）"""
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "csv":
            content = data_exporter.export_messages_to_csv(session_id, message_store)
            filename = f"messages_{session_id}_{timestamp}.csv"
            return Response(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        elif format == "json":
            content = data_exporter.export_messages_to_json(session_id, message_store)
            filename = f"messages_{session_id}_{timestamp}.json"
            return Response(
                content=content,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/end")
async def end_session(session_id: str, admin_token: Optional[str] = Cookie(None)):
    """セッションを終了"""
    # 認証チェック
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    # このセッションに接続している全ユーザーに通知
    session_end_message = {
        "type": "session_end",
        "internal_id": "system",  # システムメッセージ用の固定ID
        "message": "This session has been ended by admin.",
        "timestamp": datetime.now().isoformat()
    }
    
    # セッションに属する全クライアントを特定して通知
    clients_to_notify = [client_id for client_id, sess_id in client_sessions.items() if sess_id == session_id]
    for client_id in clients_to_notify:
        if client_id in active_connections:
            try:
                await active_connections[client_id].send_json(session_end_message)
            except Exception as e:
                print(f"Error notifying client {client_id}: {e}")
    
    # セッションを終了
    session_manager.end_session(session_id)
    return JSONResponse(content={"status": "success", "message": "Session ended"})

@app.delete("/api/sessions/{session_id}/delete")
async def delete_session(session_id: str, admin_token: Optional[str] = Cookie(None)):
    """セッションを削除"""
    # 認証チェック
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    success = session_manager.delete_session(session_id)
    if success:
        # メッセージデータも削除
        message_store.delete_session_messages(session_id)
        return JSONResponse(content={"status": "success", "message": "Session deleted"})
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.post("/api/sessions/new")
async def create_new_session(end_previous: bool = True,
                            admin_token: Optional[str] = Cookie(None)):
    """新しいセッションを作成
    
    Args:
        end_previous: Trueの場合、既存のアクティブセッションを全て終了（デフォルト）
    """
    # 認証チェック
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if end_previous:
        # 接続中の全ユーザーにセッション終了を通知
        if active_connections:
            session_end_message = {
                "type": "session_end",
                "internal_id": "system",  # システムメッセージ用の固定ID
                "message": "セッションが終了しました。新しいセッションが開始されます。",
                "timestamp": datetime.now().isoformat()
            }
            # この場合は全セッションに通知（セッションIDを指定しない）
            await broadcast_message(session_end_message)
        
        # 全てのアクティブなセッションを終了
        active_sessions = session_manager.get_active_sessions()
        for old_session in active_sessions:
            session_manager.end_session(old_session.session_id)
            print(f"Previous session ended: {old_session.session_id}")
    
    # 新しいセッションを作成
    session = session_manager.create_session()
    
    # アクティブな実験があればセッションに紐付け
    active_exp = experiment_manager.get_active_experiment()
    if active_exp:
        session.experiment_id = active_exp.experiment_id
        session_manager.update_session(session)
        # 実験の統計を再計算
        experiment_manager.recalculate_experiment_statistics(active_exp.experiment_id, session_manager)
    
    print(f"New session created: {session.session_id}")
    
    message = "New session created"
    if end_previous:
        message = "Previous sessions ended, new session created"
    
    return JSONResponse(content={
        "status": "success",
        "session": session.to_dict(),
        "message": message
    })

# ========== テンプレート管理 API ==========

@app.get("/api/ollama/models")
async def get_ollama_models(admin_token: Optional[str] = Cookie(None)):
    """Ollamaから利用可能なモデルのリストを取得"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    models = bot_manager.get_available_models()
    return JSONResponse(content={
        "models": models
    })

@app.get("/api/conditions")
async def get_conditions(admin_token: Optional[str] = Cookie(None)):
    """全条件を取得"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    conditions = condition_manager.get_all_conditions()
    return JSONResponse(content={
        "conditions": [c.to_dict() for c in conditions]
    })


@app.get("/api/conditions/{condition_id}")
async def get_condition(condition_id: str, admin_token: Optional[str] = Cookie(None)):
    """特定の条件を取得"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    condition = condition_manager.get_condition(condition_id)
    if not condition:
        raise HTTPException(status_code=404, detail="Condition not found")
    
    return JSONResponse(content=condition.to_dict())


@app.post("/api/conditions/{condition_id}/activate")
async def activate_condition(condition_id: str, admin_token: Optional[str] = Cookie(None)):
    """条件をアクティブに設定"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    condition_manager.set_active_condition(condition_id)
    
    return JSONResponse(content={
        "status": "success",
        "message": f"Condition {condition_id} is now active"
    })

@app.delete("/api/conditions/{condition_id}/delete")
async def delete_condition(condition_id: str, admin_token: Optional[str] = Cookie(None)):
    """条件を削除"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    success = condition_manager.delete_condition(condition_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete default condition")
    
    return JSONResponse(content={
        "status": "success",
        "message": "Condition deleted"
    })

# ========== 実験グループ管理 API ==========

@app.get("/api/experiments")
async def get_experiments(admin_token: Optional[str] = Cookie(None)):
    """全ての実験グループを取得"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    experiments = experiment_manager.get_all_experiments()
    return JSONResponse(content={
        "experiments": [exp.to_dict() for exp in experiments]
    })

@app.post("/api/experiments")
async def create_experiment(request: Request, admin_token: Optional[str] = Cookie(None)):
    """新しい実験グループを作成"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = await request.json()
    experiment = experiment_manager.create_experiment(
        name=data.get('name', 'New Experiment'),
        description=data.get('description', ''),
        researcher=data.get('researcher', ''),
        slug=data.get('slug', None)  # オプショナル: 指定されなければ自動生成
    )
    
    return JSONResponse(content={
        "status": "success",
        "experiment": experiment.to_dict()
    })

@app.post("/api/experiments/{experiment_id}/generate_codes")
async def generate_participant_codes(experiment_id: str, request: Request, admin_token: Optional[str] = Cookie(None)):
    """参加者コードを生成"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        data = await request.json()
        count = data.get('count', 0)
        
        print(f"[Codes] Generating {count} participant codes for experiment {experiment_id}")
        
        if count < 1:
            print(f"[Codes] ❌ Invalid count: {count}")
            raise HTTPException(status_code=400, detail="Count must be at least 1")
        
        experiment = experiment_manager.get_experiment(experiment_id)
        if not experiment:
            print(f"[Codes] ❌ Experiment not found: {experiment_id}")
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # 参加者コードを生成
        codes = experiment.generate_participant_codes(count)
        print(f"[Codes] ✅ Generated {len(codes)} codes")
        
        # 実験を保存
        from pathlib import Path
        experiment_manager._save_experiment(experiment, Path(experiment.data_directory))
        print(f"[Codes] ✅ Experiment saved")
        
        # 実験を再読み込みしてメモリ上のキャッシュを更新
        experiment_manager.reload_experiment(experiment_id)
        print(f"[Codes] ✅ Experiment reloaded in memory")
        
        return JSONResponse(content={
            "status": "success",
            "codes": codes,
            "count": len(codes)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Codes] ❌ Error generating participant codes: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Note: More specific paths MUST come before generic paths with parameters
@app.delete("/api/experiments/{experiment_id}/codes/unused")
async def delete_unused_codes(experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """未使用の参加者コードをすべて削除"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        experiment = experiment_manager.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # 未使用コードを削除
        unused_codes = [code for code, data in experiment.participant_codes.items() 
                       if data["status"] == "unused"]
        
        for code in unused_codes:
            del experiment.participant_codes[code]
        
        # 保存
        from pathlib import Path
        experiment_manager._save_experiment(experiment, Path(experiment.data_directory))
        
        # 実験を再読み込みしてメモリ上のキャッシュを更新
        experiment_manager.reload_experiment(experiment_id)
        
        return JSONResponse(content={
            "status": "success",
            "deleted_count": len(unused_codes),
            "deleted_codes": unused_codes
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Codes] ❌ Error deleting unused codes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/experiments/{experiment_id}/codes")
async def delete_all_codes(experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """すべての参加者コードを削除"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        experiment = experiment_manager.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # すべてのコードを削除
        count = len(experiment.participant_codes)
        experiment.participant_codes = {}
        
        # 保存
        from pathlib import Path
        experiment_manager._save_experiment(experiment, Path(experiment.data_directory))
        
        # 実験を再読み込みしてメモリ上のキャッシュを更新
        experiment_manager.reload_experiment(experiment_id)
        
        return JSONResponse(content={
            "status": "success",
            "deleted_count": count
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Codes] ❌ Error deleting all codes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/experiments/{experiment_id}/codes/{code}")
async def delete_participant_code(experiment_id: str, code: str, admin_token: Optional[str] = Cookie(None)):
    """個別の参加者コードを削除"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    print(f"[Codes] 🗑️ Delete code '{code}' for experiment: {experiment_id}")
    
    try:
        experiment = experiment_manager.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # コードを削除
        if code not in experiment.participant_codes:
            raise HTTPException(status_code=404, detail="Code not found")
        
        # 未使用のみ削除可能
        if experiment.participant_codes[code]["status"] != "unused":
            raise HTTPException(status_code=400, detail="Cannot delete code that is in use or completed")
        
        del experiment.participant_codes[code]
        
        # 保存
        from pathlib import Path
        experiment_manager._save_experiment(experiment, Path(experiment.data_directory))
        
        # 実験を再読み込みしてメモリ上のキャッシュを更新
        experiment_manager.reload_experiment(experiment_id)
        
        print(f"[Codes] ✅ Deleted code: {code}")
        
        return JSONResponse(content={"status": "success", "deleted_code": code})
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Codes] ❌ Error deleting code: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/experiments/{experiment_id}/start")
async def start_experiment(experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """実験を開始"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    experiment_manager.start_experiment(experiment_id)
    return JSONResponse(content={"status": "success"})

@app.post("/api/experiments/{experiment_id}/end")
async def end_experiment(experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """実験を終了"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    experiment_manager.end_experiment(experiment_id)
    return JSONResponse(content={"status": "success"})

@app.post("/api/experiments/{experiment_id}/pause")
async def pause_experiment(experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """実験を一時中断"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    experiment_manager.pause_experiment(experiment_id)
    return JSONResponse(content={"status": "success"})

@app.post("/api/experiments/{experiment_id}/resume")
async def resume_experiment(experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """実験を再開"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    experiment_manager.resume_experiment(experiment_id)
    return JSONResponse(content={"status": "success"})

@app.delete("/api/experiments/{experiment_id}/delete")
async def delete_experiment(experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """実験を削除"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    success = experiment_manager.delete_experiment(experiment_id)
    if success:
        return JSONResponse(content={"status": "success", "message": "Experiment deleted"})
    else:
        raise HTTPException(status_code=404, detail="Experiment not found")

@app.get("/api/experiments/{experiment_id}/conditions")
async def get_experiment_conditions(experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """実験の条件一覧を取得"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # 実験に紐づく条件を取得（is_experimentがTrueのもの）
    all_conditions = condition_manager.get_all_conditions()
    # 実験用の条件のみをフィルタ
    experiment_conditions = [c for c in all_conditions if c.is_experiment]
    
    return JSONResponse(content={
        "conditions": [c.to_dict() for c in experiment_conditions]
    })

@app.post("/api/experiments/{experiment_id}/conditions")
async def create_experiment_condition(
    experiment_id: str,
    request: Request,
    admin_token: Optional[str] = Cookie(None)
):
    """実験の条件を作成"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = await request.json()
    
    # Conditionオブジェクトを作成
    condition = Condition(
        condition_id=data.get('condition_id') or f"condition_{uuid.uuid4().hex[:12]}",
        name=data['name'],
        description=data.get('description'),
        bot_model=data['bot_model'],
        system_prompt=data['system_prompt'],
        is_experiment=True,
        experiment_group=data.get('experiment_group') or data['name'],
        weight=data.get('weight', 1),
        auto_create_session=data.get('auto_create_session', True),
        end_previous_session=data.get('end_previous_session', False),
        instruction_text=data.get('instruction_text'),
        time_limit_minutes=data.get('time_limit_minutes')
    )
    
    condition_manager.save_condition(condition)
    
    # ✅ 新機能: 条件を実験のtemplate_idsに自動追加
    experiment = experiment_manager.get_experiment(experiment_id)
    if experiment:
        if condition.condition_id not in experiment.template_ids:
            experiment.template_ids.append(condition.condition_id)
            from pathlib import Path
            data_dir = Path(experiment.data_directory)
            experiment_manager._save_experiment(experiment, data_dir)
            print(f"[Condition] ✅ Auto-added to experiment template_ids: {condition.name}")
    
    return JSONResponse(content={
        "status": "success",
        "condition": condition.to_dict()
    })

@app.get("/api/experiments/{experiment_id}/sessions")
async def get_experiment_sessions(experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """実験のセッション一覧を取得"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    all_sessions = session_manager.get_all_sessions()
    exp_sessions = [s for s in all_sessions if s.experiment_id == experiment_id]
    
    return JSONResponse(content={
        "sessions": [s.to_dict() for s in exp_sessions]
    })

@app.get("/api/experiments/{experiment_id}/statistics")
async def get_experiment_statistics(experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """実験の統計情報を取得"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # 実験に属するすべてのセッションを取得
    all_sessions = session_manager.get_all_sessions()
    exp_sessions = [s for s in all_sessions if s.experiment_id == experiment_id]
    
    # 条件ごとの統計を計算
    condition_stats = {}
    for session in exp_sessions:
        condition = session.experiment_group or "No Condition"
        if condition not in condition_stats:
            condition_stats[condition] = {
                "condition_name": condition,
                "session_count": 0,
                "participant_count": 0,
                "message_count": 0
            }
        condition_stats[condition]["session_count"] += 1
        condition_stats[condition]["participant_count"] += len(session.participants)
        condition_stats[condition]["message_count"] += session.total_messages
    
    return JSONResponse(content={
        "experiment_id": experiment_id,
        "total_sessions": len(exp_sessions),
        "condition_stats": list(condition_stats.values())
    })

@app.post("/api/experiments/{experiment_id}/flow")
async def save_experiment_flow(experiment_id: str, request: Request, admin_token: Optional[str] = Cookie(None)):
    """🆕 実験レベルのフローを保存"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        data = await request.json()
        experiment_flow = data.get('experiment_flow', [])
        
        # 実験を取得
        experiment = experiment_manager.get_experiment(experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # experiment_flowを更新
        experiment.experiment_flow = experiment_flow
        
        # 保存
        from pathlib import Path
        data_dir = Path(experiment.data_directory)
        experiment_manager._save_experiment(experiment, data_dir)
        
        # 実験を再読み込みしてメモリ上のキャッシュを更新
        experiment_manager.reload_experiment(experiment_id)
        
        print(f"[Flow] Saved {len(experiment_flow)} steps | {experiment.name}")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Experiment flow saved successfully",
            "step_count": len(experiment_flow)
        })
        
    except Exception as e:
        print(f"[Experiment] Error saving flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== アンケート回答 API ==========

@app.post("/api/sessions/{session_id}/survey")
async def submit_survey_response(session_id: str, request: Request):
    """アンケート回答を保存（旧形式、後方互換性のため残す）"""
    try:
        data = await request.json()
        client_id = data.get('client_id')
        responses = data.get('responses', [])
        
        if not client_id:
            raise HTTPException(status_code=400, detail="client_id is required")
        
        # セッションを取得
        session = session_manager.load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 回答をSurveyResponseオブジェクトに変換
        survey_responses = [
            SurveyResponse(
                question_id=resp['question_id'],
                answer=resp['answer']
            )
            for resp in responses
        ]
        
        # セッションに回答を保存
        session.add_survey_response(client_id, survey_responses)
        session_manager.update_session(session)
        
        print(f"[Survey] 📝 Survey responses saved for {client_id} in session {session_id}")
        print(f"   Total responses: {len(survey_responses)}")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Survey responses saved successfully",
            "response_count": len(survey_responses)
        })
        
    except Exception as e:
        print(f"[Survey] Error saving survey response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== 🆕 多段階実験フロー API ==========

@app.get("/api/sessions/{session_id}/flow/current")
async def get_current_step(session_id: str, client_id: str = None):
    """現在のステップ情報を取得"""
    try:
        # セッションを取得
        session = session_manager.load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 🆕 完了済み参加者チェック
        if client_id and session.is_participant_completed(client_id):
            return JSONResponse(content={
                "already_completed": True,
                "message": "You have already completed this experiment. Thank you for your participation!"
            })
        
        # 実験レベルのフローを取得（フローベースシステム）
        if not session.experiment_id:
            return JSONResponse(content={
                "has_flow": False,
                "message": "No experiment configured for this session"
            })
        
        experiment = experiment_manager.get_experiment(session.experiment_id)
        if not experiment:
            return JSONResponse(content={
                "has_flow": False,
                "message": "Experiment not found"
            })
        
        if not experiment.experiment_flow or len(experiment.experiment_flow) == 0:
            return JSONResponse(content={
                "has_flow": False,
                "message": "No experiment flow configured"
            })
        
        # 実験フローをExperimentStepオブジェクトに変換
        from .models.condition import ExperimentStep
        effective_flow = [ExperimentStep.from_dict(step) for step in experiment.experiment_flow]
        print(f"[Flow] Using experiment-level flow ({len(effective_flow)} steps)")
        
        # 現在のステップを取得
        if session.current_step_index >= len(effective_flow):
            # すべてのステップが完了
            return JSONResponse(content={
                "has_flow": True,
                "completed": True,
                "message": "All steps completed"
            })
        
        current_step = effective_flow[session.current_step_index]
        
        return JSONResponse(content={
            "has_flow": True,
            "completed": False,
            "current_step_index": session.current_step_index,
            "total_steps": len(effective_flow),
            "current_step": current_step.to_dict(),
            "completed_steps": session.completed_steps
        })
        
    except Exception as e:
        print(f"[Flow] Error getting current step: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/flow/advance")
async def advance_step(session_id: str, request: Request):
    """次のステップに進む"""
    try:
        data = await request.json()
        client_id = data.get('client_id')
        step_response = data.get('response')  # ステップの回答データ
        
        if not client_id:
            raise HTTPException(status_code=400, detail="client_id is required")
        
        # セッションを取得
        session = session_manager.load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 実験を取得（フローベースシステム）
        if not session.experiment_id:
            raise HTTPException(status_code=400, detail="No experiment configured for this session")
        
        experiment = experiment_manager.get_experiment(session.experiment_id)
        if not experiment:
            raise HTTPException(status_code=400, detail="Experiment not found")
        
        if not experiment.experiment_flow or len(experiment.experiment_flow) == 0:
            raise HTTPException(status_code=400, detail="No experiment flow configured")
        
        # 実験フローをExperimentStepオブジェクトに変換
        from .models.condition import ExperimentStep
        effective_flow = [ExperimentStep.from_dict(step) for step in experiment.experiment_flow]
        print(f"[Flow] Using experiment-level flow ({len(effective_flow)} steps)")
        
        # 現在のステップを完了としてマーク
        if session.current_step_index < len(effective_flow):
            current_step = effective_flow[session.current_step_index]
            session.complete_step(current_step.step_id)
            
            # 回答データを保存
            if step_response:
                session.add_step_response(current_step.step_id, client_id, step_response)
            
            print(f"[Flow] Step '{current_step.step_id}' completed by {client_id}")
        
        # 次のステップに進む
        session.advance_step()
        session_manager.update_session(session)
        
        # 次のステップ情報を返す
        if session.current_step_index >= len(effective_flow):
            # 🆕 参加者を完了としてマーク
            session.mark_participant_completed(client_id)
            session_manager.update_session(session)
            print(f"[Flow] Participant {client_id} marked as completed")
            
            # 🆕 参加者コードを "completed" としてマーク
            if session.participant_code and session.experiment_id:
                experiment = experiment_manager.get_experiment(session.experiment_id)
                if experiment:
                    experiment.mark_code_completed(session.participant_code)
                    from pathlib import Path
                    experiment_manager._save_experiment(experiment, Path(experiment.data_directory))
                    print(f"[Flow] Participant code '{session.participant_code}' marked as completed")
            
            return JSONResponse(content={
                "status": "success",
                "completed": True,
                "message": "All steps completed"
            })
        
        next_step = effective_flow[session.current_step_index]
        next_step_dict = next_step.to_dict()
        
        # 🆕 ブランチステップの場合、ランダムにパスを選択してそのステップを返す
        if next_step.step_type == 'branch':
            # 元のJSONデータからbranchesを取得
            original_step_data = experiment.experiment_flow[session.current_step_index]
            branches = original_step_data.get('branches', [])
            
            if branches:
                import random
                # ランダムにbranchを選択（weightを考慮）
                selected_branch = random.choice(branches)
                print(f"[Flow] Branch '{next_step.step_id}' selected path: {selected_branch.get('branch_id', 'unknown')}")
                
                # ブランチの最初のステップを取得
                branch_steps = selected_branch.get('steps', [])
                if branch_steps:
                    from .models.condition import ExperimentStep
                    branch_step = ExperimentStep.from_dict(branch_steps[0])
                    
                    # ブランチ選択情報をセッションに保存
                    session.add_step_response(next_step.step_id, client_id, {
                        "branch_selected": selected_branch.get('branch_id'),
                        "condition_label": selected_branch.get('condition_label')
                    })
                    session_manager.update_session(session)
                    
                    return JSONResponse(content={
                        "status": "success",
                        "completed": False,
                        "current_step_index": session.current_step_index,
                        "next_step": branch_step.to_dict(),
                        "is_branch_step": True
                    })
        
        return JSONResponse(content={
            "status": "success",
            "completed": False,
            "current_step_index": session.current_step_index,
            "next_step": next_step_dict
        })
        
    except Exception as e:
        print(f"[Flow] Error advancing step: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/ai_evaluate")
async def ai_evaluate_chat(session_id: str, request: Request):
    """AIによるチャット評価"""
    try:
        data = await request.json()
        client_id = data.get('client_id')
        step_id = data.get('step_id')
        evaluation_config = data.get('evaluation_config', {})
        
        if not client_id or not step_id:
            raise HTTPException(status_code=400, detail="client_id and step_id are required")
        
        import ollama
        import re
        from pathlib import Path
        import json
        
        # セッションを取得
        session = session_manager.load_session(session_id)
        if not session or not session.experiment_id:
            raise HTTPException(status_code=404, detail="Session or experiment not found")
        
        experiment = experiment_manager.get_experiment(session.experiment_id)
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # メッセージファイルを読み込み
        messages_file = Path(experiment.data_directory) / "messages" / f"{session_id}.json"
        if not messages_file.exists():
            raise HTTPException(status_code=404, detail="No messages found for this session")
        
        with open(messages_file, 'r', encoding='utf-8') as f:
            messages_data = json.load(f)
        
        # ユーザーとボットのメッセージのみを抽出
        conversation = []
        for msg in messages_data.get('messages', []):
            if msg.get('type') in ['user', 'bot']:
                role = "ユーザー" if msg['type'] == 'user' else "AI"
                conversation.append(f"{role}: {msg.get('message', '')}")
        
        if len(conversation) < 2:
            raise HTTPException(status_code=400, detail="Not enough messages to evaluate")
        
        conversation_text = "\n".join(conversation)
        
        # 評価質問を取得（設定から）
        questions = evaluation_config.get('questions', [])
        evaluation_model = evaluation_config.get('evaluation_model', 'gemma2:9b')
        context_prompt = evaluation_config.get('context_prompt', '')
        
        # デフォルト質問（設定がない場合）
        if not questions:
            questions = [
                {"question_id": "q1", "text": "ユーザーは真面目に相談をしていましたか？"},
                {"question_id": "q2", "text": "会話内容は充実していましたか？"},
                {"question_id": "q3", "text": "ユーザーは積極的に会話に参加していましたか？"},
                {"question_id": "q4", "text": "会話は意味のある内容でしたか？"}
            ]
        
        # 評価プロンプトを構築
        context_text = context_prompt if context_prompt else "以下はユーザーとAIカウンセラー/アドバイザーの会話記録です。この会話を客観的に評価してください。"
        
        questions_text = ""
        for i, q in enumerate(questions, 1):
            questions_text += f"\n{i}. {q.get('text', '')}\n   (1=全く当てはまらない、4=どちらとも言えない、7=非常に当てはまる)\n"
        
        evaluation_prompt = f"""{context_text}

【会話記録】
{conversation_text}

【評価項目】
以下の質問に1-7のリッカート尺度で回答してください。
{questions_text}

【回答形式】
必ず以下の形式で回答してください：
Q1: [1-7の数値]
Q2: [1-7の数値]
...

数値のみを記載し、他の説明は不要です。"""
        
        # AIに評価を依頼
        print(f"[AI Evaluation] Evaluating chat session {session_id} using {evaluation_model}...")
        response = ollama.chat(
            model=evaluation_model,
            messages=[{"role": "user", "content": evaluation_prompt}]
        )
        
        ai_response = response['message']['content']
        print(f"[AI Evaluation] AI response: {ai_response}")
        
        # 回答をパース
        evaluation_results = {}
        for i in range(1, len(questions) + 1):
            match = re.search(rf'Q{i}:\s*(\d+)', ai_response)
            if match:
                score = int(match.group(1))
                if 1 <= score <= 7:
                    q_id = questions[i-1].get('question_id', f'q{i}')
                    evaluation_results[q_id] = score
        
        # セッションに評価結果を保存
        session.add_step_response(step_id, "ai_system", {
            "evaluation_results": evaluation_results,
            "raw_response": ai_response
        })
        session_manager.update_session(session)
        
        print(f"[AI Evaluation] Saved evaluation results: {evaluation_results}")
        
        return JSONResponse(content={
            "status": "success",
            "results": evaluation_results,
            "raw_response": ai_response
        })
        
    except Exception as e:
        print(f"[AI Evaluation] Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/flow/submit")
async def submit_step_response(session_id: str, request: Request):
    """ステップの回答を保存（進まない）"""
    try:
        data = await request.json()
        client_id = data.get('client_id')
        step_id = data.get('step_id')
        response_data = data.get('response')
        
        if not client_id or not step_id:
            raise HTTPException(status_code=400, detail="client_id and step_id are required")
        
        # セッションを取得
        session = session_manager.load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # 回答を保存
        session.add_step_response(step_id, client_id, response_data)
        session_manager.update_session(session)
        
        print(f"[Flow] Response saved for step '{step_id}' by {client_id}")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Response saved successfully"
        })
        
    except Exception as e:
        print(f"[Flow] Error saving step response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/{session_id}/chat/configure")
async def configure_chat(session_id: str, request: Request):
    """チャットステップのbot設定を適用"""
    try:
        data = await request.json()
        bot_model = data.get('bot_model', 'gemma3:4b')
        system_prompt = data.get('system_prompt', '')
        temperature = data.get('temperature', 0.7)
        top_p = data.get('top_p', 0.9)
        top_k = data.get('top_k', 40)
        repeat_penalty = data.get('repeat_penalty', 1.1)
        num_predict = data.get('num_predict')
        
        # セッションを取得
        session = session_manager.load_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # bot_managerに設定を適用
        bot_manager.set_model(session_id, bot_model)
        bot_manager.set_system_prompt(session_id, system_prompt)
        bot_manager.set_temperature(session_id, temperature)
        bot_manager.set_top_p(session_id, top_p)
        bot_manager.set_top_k(session_id, top_k)
        bot_manager.set_repeat_penalty(session_id, repeat_penalty)
        bot_manager.set_num_predict(session_id, num_predict)
        
        print(f"[Chat] {bot_model} | T:{temperature} P:{top_p} K:{top_k} RP:{repeat_penalty}")
        
        return JSONResponse(content={
            "status": "success",
            "message": "Chat configuration applied",
            "config": {
                "bot_model": bot_model,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repeat_penalty": repeat_penalty,
                "num_predict": num_predict
            }
        })
        
    except Exception as e:
        print(f"[Chat Config] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}/survey")
async def get_survey_responses(session_id: str, admin_token: Optional[str] = Cookie(None)):
    """セッションのアンケート回答を取得（管理者用）"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    session = session_manager.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # アンケート回答を辞書形式に変換
    survey_data = {}
    for client_id, responses in session.survey_responses.items():
        survey_data[client_id] = [resp.to_dict() for resp in responses]
    
    return JSONResponse(content={
        "session_id": session_id,
        "survey_responses": survey_data
    })

@app.get("/api/experiments/{experiment_id}/surveys")
async def get_experiment_surveys(experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """実験全体のアンケート回答を取得（管理者用）"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # 実験に属するすべてのセッションを取得
    all_sessions = session_manager.get_all_sessions()
    exp_sessions = [s for s in all_sessions if s.experiment_id == experiment_id]
    
    # 全セッションのアンケート回答を収集
    all_surveys = []
    for session in exp_sessions:
        for client_id, responses in session.survey_responses.items():
            all_surveys.append({
                "session_id": session.session_id,
                "client_id": client_id,
                "experiment_group": session.experiment_group,
                "responses": [resp.to_dict() for resp in responses]
            })
    
    return JSONResponse(content={
        "experiment_id": experiment_id,
        "total_responses": len(all_surveys),
        "survey_data": all_surveys
    })

# ========== アンケートデータエクスポート API ==========

@app.post("/api/sessions/{session_id}/export/survey")
async def export_session_survey(session_id: str, format: str = "json", 
                                admin_token: Optional[str] = Cookie(None)):
    """セッションのアンケート回答をエクスポート（直接ダウンロード）"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "csv":
            content = data_exporter.export_survey_responses_to_csv(session_id, session_manager)
            filename = f"survey_{session_id}_{timestamp}.csv"
            return Response(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        elif format == "json":
            content = data_exporter.export_survey_responses_to_json(session_id, session_manager)
            filename = f"survey_{session_id}_{timestamp}.json"
            return Response(
                content=content,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/experiments/{experiment_id}/export/survey")
async def export_experiment_survey(experiment_id: str, format: str = "json",
                                   admin_token: Optional[str] = Cookie(None)):
    """実験全体のアンケート回答をエクスポート（直接ダウンロード）"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "csv":
            content = data_exporter.export_experiment_survey_responses_to_csv(
                experiment_id, session_manager
            )
            filename = f"survey_experiment_{experiment_id}_{timestamp}.csv"
            return Response(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        elif format == "json":
            content = data_exporter.export_experiment_survey_responses_to_json(
                experiment_id, session_manager
            )
            filename = f"survey_experiment_{experiment_id}_{timestamp}.json"
            return Response(
                content=content,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/experiments/{experiment_id}/export/messages")
async def export_experiment_messages(experiment_id: str, format: str = "csv",
                                     admin_token: Optional[str] = Cookie(None)):
    """実験全体のメッセージデータをエクスポート（直接ダウンロード）"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        content = data_exporter.export_experiment_all_data_to_csv(
            experiment_id, session_manager, message_store
        )
        filename = f"messages_experiment_{experiment_id}_{timestamp}.csv"
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/experiments/{experiment_id}/export/sessions")
async def export_experiment_sessions_data(experiment_id: str, format: str = "csv",
                                          admin_token: Optional[str] = Cookie(None)):
    """実験全体のセッション情報をエクスポート（直接ダウンロード）"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        content = data_exporter.export_experiment_sessions_to_csv(
            experiment_id, session_manager
        )
        filename = f"sessions_experiment_{experiment_id}_{timestamp}.csv"
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/experiments/{experiment_id}/export/wide")
async def export_experiment_wide_format(experiment_id: str,
                                        admin_token: Optional[str] = Cookie(None)):
    """
    実験データをワイド形式CSVでエクスポート（統計分析用）
    1行 = 1参加者、各質問が列になる
    """
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"[Export] Exporting wide format CSV for experiment {experiment_id}")
        
        content = data_exporter.export_experiment_wide_format_csv(
            experiment_id, session_manager, message_store, experiment_manager
        )
        
        filename = f"wide_format_{experiment_id}_{timestamp}.csv"
        
        print(f"[Export] Wide format CSV generated: {len(content)} bytes")
        
        return Response(
            content=content,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        print(f"[Export] Error generating wide format CSV: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sessions/export/all")
async def export_all_sessions(format: str = "csv", admin_token: Optional[str] = Cookie(None)):
    """全セッションの情報をエクスポート（直接ダウンロード）"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "csv":
            content = data_exporter.export_all_sessions_to_csv(session_manager)
            filename = f"all_sessions_{timestamp}.csv"
            return Response(
                content=content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        elif format == "json":
            content = data_exporter.export_all_sessions_summary(session_manager)
            filename = f"all_sessions_{timestamp}.json"
            return Response(
                content=content,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid format")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))