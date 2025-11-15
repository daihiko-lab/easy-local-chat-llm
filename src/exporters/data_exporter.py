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
            'internal_id',  # 内部UUID（重複識別用）
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
    
    def export_session_summary_to_csv(self, session_id: str, session_manager: SessionManager,
                                     message_store: MessageStore) -> str:
        """セッションサマリーをCSV形式でエクスポート（文字列として返す）"""
        session_summary = session_manager.get_session_summary(session_id)
        message_stats = message_store.get_session_statistics(session_id)
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # セッション基本情報
        writer.writerow(['Section', 'Key', 'Value'])
        writer.writerow(['Session', 'session_id', session_summary['session_id']])
        writer.writerow(['Session', 'participant_code', session_summary.get('participant_code', '')])
        writer.writerow(['Session', 'created_at', session_summary['created_at']])
        writer.writerow(['Session', 'ended_at', session_summary.get('ended_at', '')])
        writer.writerow(['Session', 'status', session_summary['status']])
        writer.writerow(['Session', 'participant_count', session_summary['participant_count']])
        writer.writerow(['Session', 'participants', ', '.join(session_summary['participants'])])
        writer.writerow(['Session', 'total_messages', session_summary['total_messages']])
        writer.writerow(['Session', 'duration', session_summary.get('duration', '')])
        
        # 統計情報
        writer.writerow([])
        writer.writerow(['Statistics', 'total_messages', message_stats['total_messages']])
        writer.writerow(['Statistics', 'total_chars', message_stats['total_chars']])
        writer.writerow(['Statistics', 'total_words', message_stats['total_words']])
        
        # ユーザー別統計
        writer.writerow([])
        writer.writerow(['User Statistics', 'client_id', 'message_count', 'total_chars', 'total_words'])
        for client_id, data in message_stats['message_by_user'].items():
            writer.writerow(['User Statistics', client_id, data['count'], data['chars'], data['words']])
        
        return output.getvalue()
    
    def export_all_sessions_summary(self, session_manager: SessionManager) -> str:
        """全セッションのサマリーをエクスポート（文字列として返す）"""
        sessions = session_manager.get_all_sessions()
        
        data = {
            "total_sessions": len(sessions),
            "exported_at": datetime.now().isoformat(),
            "sessions": [session.to_dict() for session in sessions]
        }
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def export_all_sessions_to_csv(self, session_manager: SessionManager) -> str:
        """全セッションのサマリーをCSV形式でエクスポート（文字列として返す）"""
        sessions = session_manager.get_all_sessions()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー
        writer.writerow([
            'session_id',
            'participant_code',
            'created_at',
            'ended_at',
            'status',
            'participant_count',
            'participants',
            'total_messages',
            'experiment_id',
            'experiment_group',
            'condition_id'
        ])
        
        # データ行
        for session in sessions:
            writer.writerow([
                session.session_id,
                session.participant_code or '',
                session.created_at,
                session.ended_at or '',
                session.status,
                len(session.participants),
                ', '.join(session.participants),
                session.total_messages,
                session.experiment_id or '',
                session.experiment_group or '',
                session.condition_id or ''
            ])
        
        return output.getvalue()
    
    def export_complete_dataset(self, session_id: str, session_manager: SessionManager,
                               message_store: MessageStore) -> Dict[str, str]:
        """完全なデータセットをエクスポート（全てメモリ上で生成）"""
        return {
            "messages_csv": self.export_messages_to_csv(session_id, message_store),
            "messages_json": self.export_messages_to_json(session_id, message_store),
            "session_summary": self.export_session_summary(session_id, session_manager, message_store)
        }
    
    def export_complete_dataset_csv(self, session_id: str, session_manager: SessionManager,
                                    message_store: MessageStore) -> Dict[str, str]:
        """完全なデータセットをCSV形式でエクスポート（複数のCSVファイル内容を返す）"""
        return {
            "messages": self.export_messages_to_csv(session_id, message_store),
            "summary": self.export_session_summary_to_csv(session_id, session_manager, message_store),
            "contributions": self.export_user_contributions(session_id, message_store),
            "survey": self.export_survey_responses_to_csv(session_id, session_manager)
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
    
    def export_survey_responses_to_csv(self, session_id: str, session_manager: SessionManager) -> str:
        """アンケート回答をCSV形式でエクスポート（文字列として返す）"""
        session = session_manager.load_session(session_id)
        if not session or not session.survey_responses:
            # アンケート回答がない場合は空のCSVを返す
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['session_id', 'participant_code', 'client_id', 'question_id', 'answer', 'answered_at'])
            return output.getvalue()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー
        writer.writerow([
            'session_id',
            'participant_code',
            'client_id',
            'experiment_group',
            'question_id',
            'answer',
            'answered_at'
        ])
        
        # データ行
        for client_id, responses in session.survey_responses.items():
            for response in responses:
                # 回答が配列の場合はJSON文字列に変換
                answer = response.answer
                if isinstance(answer, list):
                    answer = json.dumps(answer, ensure_ascii=False)
                
                writer.writerow([
                    session_id,
                    session.participant_code or '',
                    client_id,
                    session.experiment_group or '',
                    response.question_id,
                    answer,
                    response.answered_at
                ])
        
        return output.getvalue()
    
    def export_survey_responses_to_json(self, session_id: str, session_manager: SessionManager) -> str:
        """アンケート回答をJSON形式でエクスポート（文字列として返す）"""
        session = session_manager.load_session(session_id)
        if not session:
            return json.dumps({"error": "Session not found"}, ensure_ascii=False, indent=2)
        
        data = {
            "session_id": session_id,
            "experiment_group": session.experiment_group,
            "exported_at": datetime.now().isoformat(),
            "survey_responses": {}
        }
        
        # アンケート回答を整形
        for client_id, responses in session.survey_responses.items():
            data["survey_responses"][client_id] = [resp.to_dict() for resp in responses]
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def export_experiment_survey_responses_to_csv(self, experiment_id: str, 
                                                   session_manager: SessionManager) -> str:
        """実験全体のアンケート回答をCSV形式でエクスポート（文字列として返す）"""
        # 実験に属する全セッションを取得
        all_sessions = session_manager.get_all_sessions()
        exp_sessions = [s for s in all_sessions if s.experiment_id == experiment_id]
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー
        writer.writerow([
            'experiment_id',
            'session_id',
            'participant_code',
            'client_id',
            'experiment_group',
            'condition_id',
            'question_id',
            'answer',
            'answered_at'
        ])
        
        # 各セッションのアンケート回答を出力
        for session in exp_sessions:
            for client_id, responses in session.survey_responses.items():
                for response in responses:
                    # 回答が配列の場合はJSON文字列に変換
                    answer = response.answer
                    if isinstance(answer, list):
                        answer = json.dumps(answer, ensure_ascii=False)
                    
                    writer.writerow([
                        experiment_id,
                        session.session_id,
                        session.participant_code or '',
                        client_id,
                        session.experiment_group or '',
                        session.condition_id or '',
                        response.question_id,
                        answer,
                        response.answered_at
                    ])
        
        return output.getvalue()
    
    def export_experiment_survey_responses_to_json(self, experiment_id: str,
                                                    session_manager: SessionManager) -> str:
        """実験全体のアンケート回答をJSON形式でエクスポート（文字列として返す）"""
        # 実験に属する全セッションを取得
        all_sessions = session_manager.get_all_sessions()
        exp_sessions = [s for s in all_sessions if s.experiment_id == experiment_id]
        
        data = {
            "experiment_id": experiment_id,
            "exported_at": datetime.now().isoformat(),
            "total_sessions": len(exp_sessions),
            "sessions": []
        }
        
        # 各セッションのアンケート回答を収集
        for session in exp_sessions:
            session_data = {
                "session_id": session.session_id,
                "experiment_group": session.experiment_group,
                "created_at": session.created_at,
                "survey_responses": {}
            }
            
            for client_id, responses in session.survey_responses.items():
                session_data["survey_responses"][client_id] = [resp.to_dict() for resp in responses]
            
            data["sessions"].append(session_data)
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def export_experiment_all_data_to_csv(self, experiment_id: str, 
                                          session_manager: SessionManager,
                                          message_store: MessageStore) -> str:
        """実験全体のメッセージデータをCSV形式でエクスポート（1つの大きなCSVファイル）"""
        # 実験に属する全セッションを取得
        all_sessions = session_manager.get_all_sessions()
        exp_sessions = [s for s in all_sessions if s.experiment_id == experiment_id]
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー（実験情報を追加）
        writer.writerow([
            'experiment_id',
            'session_id',
            'experiment_group',
            'message_id',
            'client_id',
            'internal_id',
            'message_type',
            'content',
            'timestamp',
            'char_count',
            'word_count'
        ])
        
        # 各セッションのメッセージを出力
        for session in exp_sessions:
            messages = message_store.get_messages_by_session(session.session_id)
            for msg in messages:
                row = [
                    experiment_id,
                    session.session_id,
                    session.experiment_group or '',
                ]
                row.extend(msg.to_csv_row())
                writer.writerow(row)
        
        return output.getvalue()
    
    def export_experiment_sessions_to_csv(self, experiment_id: str,
                                          session_manager: SessionManager) -> str:
        """実験全体のセッション情報をCSV形式でエクスポート"""
        all_sessions = session_manager.get_all_sessions()
        exp_sessions = [s for s in all_sessions if s.experiment_id == experiment_id]
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー
        writer.writerow([
            'experiment_id',
            'session_id',
            'participant_code',
            'experiment_group',
            'condition_id',
            'created_at',
            'ended_at',
            'status',
            'participant_count',
            'participants',
            'total_messages',
            'duration_seconds'
        ])
        
        # データ行
        for session in exp_sessions:
            # 継続時間を計算
            duration = ''
            if session.ended_at:
                try:
                    start = datetime.fromisoformat(session.created_at)
                    end = datetime.fromisoformat(session.ended_at)
                    duration = str((end - start).total_seconds())
                except:
                    pass
            
            writer.writerow([
                experiment_id,
                session.session_id,
                session.participant_code or '',
                session.experiment_group or '',
                session.condition_id or '',
                session.created_at,
                session.ended_at or '',
                session.status,
                len(session.participants),
                ', '.join(session.participants),
                session.total_messages,
                duration
            ])
        
        return output.getvalue()

