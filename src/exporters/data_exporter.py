import csv
import json
import io
from typing import List, Dict, Set
from datetime import datetime
from ..models.message import Message
from ..models.session import Session
from ..managers.session_manager import SessionManager
from ..managers.message_store import MessageStore
from collections import OrderedDict


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
    
    def export_experiment_wide_format_csv(self, experiment_id: str, 
                                          session_manager: SessionManager,
                                          message_store: MessageStore = None) -> str:
        """
        実験データをワイド形式CSVでエクスポート（統計分析用）
        1行 = 1参加者（1セッション）
        各質問（question_id）が列になる
        """
        # 実験に属する全セッションを取得
        all_sessions = session_manager.get_all_sessions()
        exp_sessions = [s for s in all_sessions if s.experiment_id == experiment_id and s.status == 'ended']
        
        if not exp_sessions:
            # セッションがない場合は空のCSVを返す
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['experiment_id', 'session_id', 'participant_code', 'status', 'message'])
            writer.writerow([experiment_id, '', '', 'no_data', 'No completed sessions found'])
            return output.getvalue()
        
        # すべてのquestion_idを収集（カラムヘッダー用）
        all_question_ids = OrderedDict()  # 出現順を保持
        all_ai_eval_ids = OrderedDict()   # AI評価質問ID
        
        for session in exp_sessions:
            # Survey responses
            for client_id, responses in session.survey_responses.items():
                for response in responses:
                    if response.question_id not in all_question_ids:
                        all_question_ids[response.question_id] = True
            
            # AI evaluation results (step_responses内)
            for step_id, step_data in session.step_responses.items():
                if isinstance(step_data, dict):
                    for client_id, client_data in step_data.items():
                        if isinstance(client_data, dict) and 'evaluation_results' in client_data:
                            eval_results = client_data['evaluation_results']
                            if isinstance(eval_results, dict):
                                for eval_q_id in eval_results.keys():
                                    full_id = f"ai_eval_{eval_q_id}"
                                    if full_id not in all_ai_eval_ids:
                                        all_ai_eval_ids[full_id] = True
        
        # ヘッダー行を構築
        headers = [
            'experiment_id',
            'session_id',
            'participant_code',
            'client_id',
            'condition_id',
            'experiment_group',
            'started_at',
            'ended_at',
            'duration_seconds',
            'total_messages',
            'user_message_count',
            'bot_message_count',
            'avg_user_chars',
            'avg_user_words'
        ]
        
        # サーベイ質問列を追加
        headers.extend(list(all_question_ids.keys()))
        
        # AI評価列を追加
        headers.extend(list(all_ai_eval_ids.keys()))
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        
        # 各セッションのデータを行として出力
        for session in exp_sessions:
            # 基本情報
            duration_seconds = ''
            if session.ended_at:
                try:
                    start = datetime.fromisoformat(session.created_at)
                    end = datetime.fromisoformat(session.ended_at)
                    duration_seconds = str(int((end - start).total_seconds()))
                except:
                    pass
            
            # メッセージ統計を計算
            user_msg_count = 0
            bot_msg_count = 0
            total_user_chars = 0
            total_user_words = 0
            
            if message_store:
                messages = message_store.get_messages_by_session(session.session_id)
                user_messages = [m for m in messages if m.message_type == 'user']
                bot_messages = [m for m in messages if m.message_type == 'bot']
                
                user_msg_count = len(user_messages)
                bot_msg_count = len(bot_messages)
                
                for msg in user_messages:
                    total_user_chars += msg.char_count
                    total_user_words += msg.word_count
            
            avg_user_chars = f"{total_user_chars / user_msg_count:.2f}" if user_msg_count > 0 else '0'
            avg_user_words = f"{total_user_words / user_msg_count:.2f}" if user_msg_count > 0 else '0'
            
            # client_idを取得（通常は1参加者=1セッション）
            client_id = session.participants[0] if session.participants else ''
            
            # 行データの基本部分
            row_data = [
                experiment_id,
                session.session_id,
                session.participant_code or '',
                client_id,
                session.condition_id or '',
                session.experiment_group or '',
                session.created_at,
                session.ended_at or '',
                duration_seconds,
                session.total_messages,
                user_msg_count,
                bot_msg_count,
                avg_user_chars,
                avg_user_words
            ]
            
            # サーベイ回答を追加（question_idの順番に従って）
            survey_answers = {}
            for client_id_resp, responses in session.survey_responses.items():
                for response in responses:
                    # 配列回答はJSON文字列に変換
                    answer = response.answer
                    if isinstance(answer, list):
                        answer = json.dumps(answer, ensure_ascii=False)
                    survey_answers[response.question_id] = answer
            
            for q_id in all_question_ids.keys():
                row_data.append(survey_answers.get(q_id, ''))
            
            # AI評価結果を追加
            ai_eval_answers = {}
            for step_id, step_data in session.step_responses.items():
                if isinstance(step_data, dict):
                    for client_id_resp, client_data in step_data.items():
                        if isinstance(client_data, dict) and 'evaluation_results' in client_data:
                            eval_results = client_data['evaluation_results']
                            if isinstance(eval_results, dict):
                                for eval_q_id, score in eval_results.items():
                                    full_id = f"ai_eval_{eval_q_id}"
                                    ai_eval_answers[full_id] = str(score)
            
            for eval_id in all_ai_eval_ids.keys():
                row_data.append(ai_eval_answers.get(eval_id, ''))
            
            writer.writerow(row_data)
        
        return output.getvalue()

