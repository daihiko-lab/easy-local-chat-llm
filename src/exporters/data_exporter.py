import csv
import json
import io
from typing import List, Dict
from datetime import datetime
from ..models.message import Message
from ..models.session import Session
from ..managers.session_manager import SessionManager
from ..managers.message_store import MessageStore


class DataExporter:
    """データエクスポートクラス - メモリ上で直接データを生成"""
    
    def __init__(self):
        pass  # ファイル保存しないのでディレクトリ不要
    
    def export_messages_to_csv(self, session_id: str, message_store: MessageStore) -> str:
        """メッセージをCSV形式でエクスポート（文字列として返す）"""
        messages = message_store.get_messages_by_session(session_id)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー
        writer.writerow([
            'message_id',
            'session_id',
            'client_id',
            'message_type',
            'content',
            'timestamp',
            'char_count',
            'word_count',
            'client_color'
        ])
        
        # データ行
        for msg in messages:
            writer.writerow(msg.to_csv_row())
        
        return output.getvalue()
    
    def export_messages_to_json(self, session_id: str, message_store: MessageStore) -> str:
        """メッセージをJSON形式でエクスポート（文字列として返す）"""
        messages = message_store.get_messages_by_session(session_id)
        
        data = {
            "session_id": session_id,
            "exported_at": datetime.now().isoformat(),
            "total_messages": len(messages),
            "messages": [msg.to_dict() for msg in messages]
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def export_session_summary(self, session_id: str, session_manager: SessionManager, 
                              message_store: MessageStore) -> str:
        """セッションサマリーをエクスポート（文字列として返す）"""
        session_summary = session_manager.get_session_summary(session_id)
        message_stats = message_store.get_session_statistics(session_id)
        
        data = {
            "session": session_summary,
            "statistics": message_stats,
            "exported_at": datetime.now().isoformat()
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def export_all_sessions_summary(self, session_manager: SessionManager) -> str:
        """全セッションのサマリーをエクスポート（文字列として返す）"""
        sessions = session_manager.get_all_sessions()
        
        data = {
            "total_sessions": len(sessions),
            "exported_at": datetime.now().isoformat(),
            "sessions": [session.to_dict() for session in sessions]
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def export_complete_dataset(self, session_id: str, session_manager: SessionManager,
                               message_store: MessageStore) -> Dict[str, str]:
        """完全なデータセットをエクスポート（全てメモリ上で生成）"""
        return {
            "messages_csv": self.export_messages_to_csv(session_id, message_store),
            "messages_json": self.export_messages_to_json(session_id, message_store),
            "session_summary": self.export_session_summary(session_id, session_manager, message_store)
        }
    
    def export_user_contributions(self, session_id: str, message_store: MessageStore) -> str:
        """ユーザー別の貢献度をCSVでエクスポート（文字列として返す）"""
        stats = message_store.get_session_statistics(session_id)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー
        writer.writerow([
            'client_id',
            'message_count',
            'total_chars',
            'total_words',
            'avg_chars_per_message',
            'avg_words_per_message'
        ])
        
        # データ行
        for client_id, data in stats['message_by_user'].items():
            avg_chars = data['chars'] / data['count'] if data['count'] > 0 else 0
            avg_words = data['words'] / data['count'] if data['count'] > 0 else 0
            
            writer.writerow([
                client_id,
                data['count'],
                data['chars'],
                data['words'],
                f"{avg_chars:.2f}",
                f"{avg_words:.2f}"
            ])
        
        return output.getvalue()

