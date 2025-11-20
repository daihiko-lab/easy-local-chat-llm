import json
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime
from ..models.message import Message


class MessageStore:
    """メッセージストアクラス"""
    
    def __init__(self, data_dir: str = "data/messages", experiment_manager=None):
        self.base_data_dir = Path(data_dir)
        self.experiment_manager = experiment_manager
        # ディレクトリは実際に使用する時（data_dirプロパティ）で作成される
    
    def _get_current_message_dir(self) -> Path:
        """現在のアクティブな実験のメッセージディレクトリを取得"""
        if self.experiment_manager:
            current_data_dir = self.experiment_manager.get_current_data_dir()
            message_dir = current_data_dir / "messages"
            # ベースディレクトリ以外（実験ディレクトリ）の場合のみサブディレクトリを作成
            if current_data_dir != self.experiment_manager.base_dir:
                message_dir.mkdir(parents=True, exist_ok=True)
            return message_dir
        return self.base_data_dir
    
    @property
    def data_dir(self) -> Path:
        """動的にメッセージディレクトリを取得"""
        return self._get_current_message_dir()
    
    def save_message(self, message: Message):
        """メッセージを保存"""
        # セッションごとにファイルを分ける
        session_file = self.data_dir / f"{message.session_id}.json"
        
        # 既存のメッセージをロード
        messages = []
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                try:
                    messages = json.load(f)
                except json.JSONDecodeError:
                    messages = []
        
        # 新しいメッセージを追加
        messages.append(message.to_dict())
        
        # ファイルに保存
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
    
    def get_messages_by_session(self, session_id: str) -> List[Message]:
        """セッションIDでメッセージを取得"""
        session_file = self.data_dir / f"{session_id}.json"
        if not session_file.exists():
            return []
        
        with open(session_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return [Message.from_dict(msg) for msg in data]
            except json.JSONDecodeError:
                return []
    
    def get_messages_by_client(self, session_id: str, client_id: str) -> List[Message]:
        """特定のクライアントのメッセージを取得"""
        messages = self.get_messages_by_session(session_id)
        return [msg for msg in messages if msg.client_id == client_id]
    
    def get_messages_by_type(self, session_id: str, message_type: str) -> List[Message]:
        """メッセージタイプで絞り込み"""
        messages = self.get_messages_by_session(session_id)
        return [msg for msg in messages if msg.message_type == message_type]
    
    def get_messages_count(self, session_id: str) -> int:
        """セッションのメッセージ数を取得"""
        return len(self.get_messages_by_session(session_id))
    
    def get_all_messages(self) -> List[Message]:
        """全てのメッセージを取得"""
        all_messages = []
        for message_file in self.data_dir.glob("*.json"):
            try:
                with open(message_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_messages.extend([Message.from_dict(msg) for msg in data])
            except Exception as e:
                print(f"Error loading messages from {message_file}: {e}")
        
        # タイムスタンプでソート
        all_messages.sort(key=lambda m: m.timestamp)
        return all_messages
    
    def get_session_statistics(self, session_id: str) -> Dict:
        """セッションの統計情報を取得"""
        messages = self.get_messages_by_session(session_id)
        
        if not messages:
            return {
                "total_messages": 0,
                "total_chars": 0,
                "total_words": 0,
                "participants": [],
                "message_by_user": {}
            }
        
        # 参加者ごとのメッセージ数を集計
        message_by_user = {}
        total_chars = 0
        total_words = 0
        participants = set()
        
        for msg in messages:
            if msg.message_type == "message":
                participants.add(msg.client_id)
                if msg.client_id not in message_by_user:
                    message_by_user[msg.client_id] = {
                        "count": 0,
                        "chars": 0,
                        "words": 0
                    }
                
                message_by_user[msg.client_id]["count"] += 1
                message_by_user[msg.client_id]["chars"] += msg.metadata.char_count
                message_by_user[msg.client_id]["words"] += msg.metadata.word_count
                
                total_chars += msg.metadata.char_count
                total_words += msg.metadata.word_count
        
        return {
            "total_messages": len([m for m in messages if m.message_type == "message"]),
            "total_chars": total_chars,
            "total_words": total_words,
            "participants": list(participants),
            "message_by_user": message_by_user
        }
    
    def delete_session_messages(self, session_id: str) -> bool:
        """セッションのメッセージを削除"""
        session_file = self.data_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        return False
    
    def search_messages(self, session_id: str, keyword: str) -> List[Message]:
        """メッセージを検索"""
        messages = self.get_messages_by_session(session_id)
        return [msg for msg in messages if keyword.lower() in msg.content.lower()]

