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
from datetime import datetime
from pathlib import Path

from .models.session import Session
from .models.message import Message
from .models.condition import Condition
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

# 接続中のクライアントを保持する辞書
# key: 接続ID（ユニーク）, value: WebSocket接続
active_connections: Dict[str, WebSocket] = {}
client_colors: Dict[str, str] = {} # クライアントIDと色の対応を保持
client_sessions: Dict[str, str] = {} # 接続IDとセッションIDの対応を保持
connection_to_display_name: Dict[str, str] = {} # 接続ID→表示名のマッピング
connection_to_base_name: Dict[str, str] = {} # 接続ID→ベース名のマッピング

# 実験管理のインスタンス（最初に初期化）
experiment_manager = ExperimentManager()

# 現在のデータディレクトリを取得
current_data_dir = experiment_manager.get_current_data_dir()

# データ管理のインスタンス（タイムスタンプフォルダを使用）
session_manager = SessionManager(data_dir=str(current_data_dir / "sessions"))
message_store = MessageStore(data_dir=str(current_data_dir / "messages"))
data_exporter = DataExporter()
condition_manager = ConditionManager(condition_file=str(current_data_dir / "conditions" / "conditions.json"))

# ボット管理のインスタンス（モデルは各セッション作成時に条件から設定）
bot_manager = BotManager(bot_client_id="bot")

# 管理者認証用
ADMIN_CREDENTIALS_FILE = "data/admin_credentials.json"
admin_tokens: Dict[str, bool] = {}  # トークン: 認証済みフラグ

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
        return False
    return admin_tokens.get(token, False)

# アプリケーション起動時の処理
@app.on_event("startup")
async def startup_event():
    global session_manager, bot_manager, experiment_manager, current_data_dir
    
    # 起動情報を表示
    print("\n" + "="*60)
    print("APPLICATION STARTUP")
    print("="*60)
    print(f"📁 Data Directory: {current_data_dir}")
    print(f"   ├─ Experiments: {current_data_dir / 'experiments'}")
    print(f"   ├─ Conditions: {current_data_dir / 'conditions'}")
    print(f"   ├─ Sessions: {current_data_dir / 'sessions'}")
    print(f"   └─ Messages: {current_data_dir / 'messages'}")
    print("="*60 + "\n")
    
    # Ollamaサービスの可用性をチェック
    print("\n" + "="*60)
    print("OLLAMA SERVICE CHECK")
    print("="*60)
    try:
        import ollama
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
    print(f"Root:         http://localhost:8000/")
    print(f"Admin Panel:  http://localhost:8000/admin")
    print(f"User Login:   http://localhost:8000/login")
    print("="*60 + "\n")

@app.get("/")
async def get(request: Request):
    # アクティブなセッションがあるかチェック
    active_sessions = session_manager.get_active_sessions()
    
    if not active_sessions:
        # アクティブなセッションがない場合は管理画面にリダイレクト
        return RedirectResponse(url="/admin", status_code=302)
    
    # ログイン画面にリダイレクト
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login")
async def login_page(request: Request):
    """ログイン画面"""
    return templates.TemplateResponse("login.html", {
        "request": request
    })

@app.get("/api/connection/status")
async def get_connection_status():
    """現在の接続状況を取得（実験の同時セッション数制限も考慮）"""
    # 管理者ビューワー以外の接続数をカウント
    non_admin_connections = [
        cid for cid in active_connections.keys() 
        if not cid.startswith("admin_viewer_")
    ]
    
    # アクティブな実験の同時セッション数制限をチェック
    active_exp = experiment_manager.get_active_experiment()
    can_join = True
    reason = ""
    waiting_info = None
    
    if active_exp:
        can_create, error_msg = experiment_manager.can_create_session(
            active_exp.experiment_id, 
            session_manager
        )
        if not can_create:
            can_join = False
            reason = error_msg
            # 待機情報を追加
            if active_exp.max_concurrent_sessions:
                active_count = experiment_manager.get_active_session_count(
                    active_exp.experiment_id, 
                    session_manager
                )
                waiting_info = {
                    "current_sessions": active_count,
                    "max_sessions": active_exp.max_concurrent_sessions,
                    "experiment_name": active_exp.name
                }
    
    return JSONResponse(content={
        "active_users": len(non_admin_connections),
        "is_available": can_join,
        "max_users": 1,
        "reason": reason,
        "waiting_info": waiting_info
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
async def chat(request: Request, client_id: str, session_id: str = None, 
               session_password: str = None, user_password: str = None, auto_create: bool = False):
    # auto_createフラグがある場合、テンプレートから新しいセッションを作成
    if auto_create:
        try:
            # アクティブな実験の同時セッション数制限をチェック
            active_exp = experiment_manager.get_active_experiment()
            if active_exp:
                can_create, error_msg = experiment_manager.can_create_session(
                    active_exp.experiment_id, 
                    session_manager
                )
                if not can_create:
                    # 制限に達している場合はログインページにリダイレクト
                    print(f"[Session] Cannot create session: {error_msg}")
                    return RedirectResponse(url="/login", status_code=302)
            
            # 常に実験用条件からランダムに選択
            session, condition = condition_manager.create_session_from_condition(
                session_manager,
                experiment_manager=experiment_manager,  # 実験マネージャーを渡す
                use_random_experiment=True  # 常に実験モード
            )
            session_id = session.session_id
            
            # 条件のボット設定を適用（セッションごとに独立）
            bot_manager.set_model(session_id, condition.bot_model)
            if condition.system_prompt:  # システムプロンプトが設定されている場合のみ適用
                bot_manager.set_system_prompt(session_id, condition.system_prompt)
            
            # ログメッセージ
            if condition.is_experiment:
                print(f"[Experiment] New session created | Condition: {condition.experiment_group} | Session: {session_id}")
            else:
                print(f"[Session] New session created from condition: {session_id}")
        except Exception as e:
            print(f"[Auto-Create] Error creating session: {e}")
            # エラー時は通常フローに戻る
            auto_create = False
    
    # session_idが指定されていない場合は、現在のセッションを使用
    if not session_id:
        current_session = session_manager.get_current_session()
        session_id = current_session.session_id if current_session else "no_session"
        session = current_session
    else:
        # 指定されたセッションが存在するか確認
        session = session_manager.load_session(session_id)
        if not session or session.status != "active":
            # セッションが存在しないか終了している場合は、現在のセッションを使用
            current_session = session_manager.get_current_session()
            session_id = current_session.session_id if current_session else "no_session"
            session = current_session
    
    # セッション全体のパスワード保護チェック
    if session and session.password_protected:
        if not session_password or not session.verify_password(session_password):
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "セッションパスワードが正しくありません"
            })
    
    # ユーザーIDのパスワード保護チェック
    if session:
        # 既存の保護されたIDの場合
        if session.has_user_password(client_id):
            if not user_password or not session.verify_user_password(client_id, user_password):
                return templates.TemplateResponse("login.html", {
                    "request": request,
                    "error": f"ユーザーID '{client_id}' のパスワードが正しくありません"
                })
        # セッションがユーザーパスワード必須の場合、新規ユーザーもパスワードが必要
        elif session.require_user_password and not session.has_user_password(client_id):
            if not user_password:
                return templates.TemplateResponse("login.html", {
                    "request": request,
                    "error": "このセッションではユーザーパスワードが必須です"
                })
    
    return templates.TemplateResponse("chat.html", {
        "request": request, 
        "client_id": client_id,
        "session_id": session_id
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
    
    print(f"[Viewer] Admin connected to session: {session_id}")
    
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
        print(f"[Viewer] Admin disconnected from session: {session_id}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str = None):
    await websocket.accept()
    client_id = None
    
    # session_idが指定されている場合は、そのセッションを使用
    if session_id:
        session = session_manager.load_session(session_id)
        if not session or session.status != "active":
            await websocket.close(code=1000, reason="Invalid or inactive session")
            return
    else:
        # 指定されていない場合は現在のセッションを使用
        current_session = session_manager.get_current_session()
        if not current_session:
            await websocket.close(code=1000, reason="No active session")
            return
        session_id = current_session.session_id
    
    try:
        while True:
            data = await websocket.receive_json()
            if not client_id:
                # クライアントIDがまだ設定されていない場合、初期メッセージから取得
                if "client_id" in data:
                    base_client_id = data["client_id"]
                    
                    # 管理者ビューワー以外の接続数をチェック（1人制限）
                    non_admin_connections = [
                        cid for cid in active_connections.keys() 
                        if not cid.startswith("admin_viewer_")
                    ]
                    
                    if len(non_admin_connections) >= 1:
                        # 既に1人接続している場合は拒否
                        print(f"Connection limit reached. User {base_client_id} was rejected.")
                        await websocket.close(code=1000, reason="Only one user allowed")
                        return
                    
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
                    
                    print(f"[Connection] User '{display_name}' connected (connection_id: {connection_id})")
                    
                    active_connections[client_id] = websocket
                    client_sessions[client_id] = session_id  # セッションIDを記録
                    
                    # セッションに参加者を追加（表示名を使用）
                    session_manager.add_participant(session_id, display_name)
                    
                    # 実験の参加者数を更新
                    session = session_manager.get_session(session_id)
                    if session and session.experiment_id:
                        experiment_manager.update_participant_count(session.experiment_id)
                    
                    # システムメッセージを作成・保存
                    join_message = Message(
                        session_id=session_id,
                        client_id=display_name,
                        message_type="system",
                        content=f"Client {display_name} has joined the room",
                        timestamp=data["timestamp"]
                    )
                    message_store.save_message(join_message)
                    
                    message = {
                        "type": "system",
                        "message": f"Client {display_name} has joined the room",
                        "timestamp": data["timestamp"]
                    }
                    await broadcast_message(message)
                else:
                    print("No client_id provided in initial message")
                    await websocket.close(code=1000, reason="client_id required")
                    return
            elif data["type"] == "message":
                # 表示名を取得
                display_name = connection_to_display_name.get(client_id, client_id)
                
                # ユーザーメッセージを保存
                user_message = Message(
                    session_id=session_id,
                    client_id=display_name,
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
                    "message": data["message"],
                    "timestamp": data["timestamp"],
                }
                await broadcast_message(message)
                
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
                            "message": bot_response,
                            "timestamp": bot_message_obj.timestamp,
                        }
                        await broadcast_message(bot_broadcast)
                        
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
                message_type="system",
                content=f"Client {display_name} has left the room",
                timestamp=datetime.now().isoformat()
            )
            message_store.save_message(leave_message)
            
            message = {
                "type": "system",
                "message": f"Client {display_name} has left the room",
                "timestamp": datetime.now().isoformat()
            }
            await broadcast_message(message)

async def broadcast_message(message: dict):
    """全ての接続中のクライアントにメッセージをブロードキャストする"""
    for connection in active_connections.values():
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

@app.post("/api/sessions/{session_id}/set_user_password")
async def set_user_password(session_id: str, client_id: str, password: str):
    """ユーザーIDにパスワードを設定"""
    session = session_manager.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.set_user_password(client_id, password)
    session_manager.update_session(session)
    
    return JSONResponse(content={
        "status": "success",
        "message": f"Password set for user {client_id}"
    })

@app.get("/api/sessions/{session_id}/check_user_password")
async def check_user_password(session_id: str, client_id: str):
    """ユーザーIDがパスワード保護されているか確認"""
    session = session_manager.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return JSONResponse(content={
        "has_password": session.has_user_password(client_id),
        "protected_users": session.get_protected_users()
    })

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
async def create_new_session(end_previous: bool = True, password: Optional[str] = None,
                            require_user_password: bool = False,
                            disable_user_password: bool = False,
                            admin_token: Optional[str] = Cookie(None)):
    """新しいセッションを作成
    
    Args:
        end_previous: Trueの場合、既存のアクティブセッションを全て終了（デフォルト）
        password: セッションのパスワード（オプション）
        require_user_password: ユーザーパスワード必須（True=必須、False=任意）
        disable_user_password: ユーザーパスワード完全無効（True=パスワードなし強制）
    """
    # 認証チェック
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if end_previous:
        # 接続中の全ユーザーにセッション終了を通知
        if active_connections:
            session_end_message = {
                "type": "session_end",
                "message": "セッションが終了しました。新しいセッションが開始されます。",
                "timestamp": datetime.now().isoformat()
            }
            await broadcast_message(session_end_message)
        
        # 全てのアクティブなセッションを終了
        active_sessions = session_manager.get_active_sessions()
        for old_session in active_sessions:
            session_manager.end_session(old_session.session_id)
            print(f"Previous session ended: {old_session.session_id}")
    
    # 新しいセッションを作成
    session = session_manager.create_session(
        password=password, 
        require_user_password=require_user_password,
        disable_user_password=disable_user_password
    )
    password_status = "with password" if password else "without password"
    user_pw_status = "required" if require_user_password else "optional" if not disable_user_password else "disabled"
    print(f"New session created: {session.session_id} ({password_status}, user password: {user_pw_status})")
    
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
        researcher=data.get('researcher', '')
    )
    
    # 同時セッション数制限を設定
    if 'max_concurrent_sessions' in data and data['max_concurrent_sessions'] is not None:
        experiment.max_concurrent_sessions = data['max_concurrent_sessions']
        # 実験を保存し直す
        from pathlib import Path
        data_dir = Path(experiment.data_directory)
        experiment_manager._save_experiment(experiment, data_dir)
    
    return JSONResponse(content={
        "status": "success",
        "experiment": experiment.to_dict()
    })

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

@app.post("/api/experiments/{experiment_id}/update_limit")
async def update_experiment_limit(request: Request, experiment_id: str, admin_token: Optional[str] = Cookie(None)):
    """実験の同時セッション数制限を更新"""
    if not verify_admin_token(admin_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    data = await request.json()
    max_concurrent_sessions = data.get('max_concurrent_sessions')
    
    # 実験を取得
    experiment = experiment_manager.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # 制限を更新
    experiment.max_concurrent_sessions = max_concurrent_sessions
    
    # 保存
    from pathlib import Path
    data_dir = Path(experiment.data_directory)
    experiment_manager._save_experiment(experiment, data_dir)
    
    print(f"[Experiment] Updated concurrent limit for {experiment_id}: {max_concurrent_sessions}")
    
    return JSONResponse(content={
        "status": "success",
        "max_concurrent_sessions": max_concurrent_sessions
    })

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
        end_previous_session=data.get('end_previous_session', False)
    )
    
    condition_manager.save_condition(condition)
    
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
        condition_stats[condition]["participant_count"] += session.participant_count
        condition_stats[condition]["message_count"] += session.total_messages
    
    return JSONResponse(content={
        "experiment_id": experiment_id,
        "total_sessions": len(exp_sessions),
        "condition_stats": list(condition_stats.values())
    })