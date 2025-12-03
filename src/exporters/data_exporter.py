import csv
import json
import io
import zipfile
from typing import List, Dict, Set, Optional, Any, Tuple
from datetime import datetime
from ..models.message import Message
from ..models.session import Session
from ..managers.session_manager import SessionManager
from ..managers.message_store import MessageStore
from ..managers.experiment_manager import ExperimentManager
from collections import OrderedDict

# UTF-8 BOM（Excelで日本語を正しく認識させるため）
UTF8_BOM = '\ufeff'

# 欠損値の表現オプション
MISSING_VALUE_OPTIONS = {
    'blank': '',      # 空文字列
    'NA': 'NA',       # NA文字列
    'dot': '.',       # ピリオド（SAS/Stata形式）
}


class DataExporter:
    """データエクスポートクラス - メモリ上で直接データを生成"""
    
    def __init__(self):
        pass  # ファイル保存しないのでディレクトリ不要
    
    def _add_bom_if_excel(self, content: str, excel_format: bool = False) -> str:
        """Excel形式の場合はBOMを追加"""
        if excel_format:
            return UTF8_BOM + content
        return content
    
    def _get_missing_value(self, missing_value_style: str = 'blank') -> str:
        """欠損値の表現を取得"""
        return MISSING_VALUE_OPTIONS.get(missing_value_style, '')
    
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
                # 回答が配列の場合はJSON文字列に変換、文字列の場合は改行を置換
                answer = response.answer
                if isinstance(answer, list):
                    answer = json.dumps(answer, ensure_ascii=False)
                elif isinstance(answer, str):
                    # 改行をスペースに置換（CSVの行分割を防ぐ）
                    answer = answer.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
                
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
                    # 回答が配列の場合はJSON文字列に変換、文字列の場合は改行を置換
                    answer = response.answer
                    if isinstance(answer, list):
                        answer = json.dumps(answer, ensure_ascii=False)
                    elif isinstance(answer, str):
                        # 改行をスペースに置換（CSVの行分割を防ぐ）
                        answer = answer.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
                    
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
            'assigned_conditions',
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
            
            # 割り当てられた条件をJSON文字列に変換
            assigned_conditions_str = ''
            if hasattr(session, 'assigned_conditions') and session.assigned_conditions:
                assigned_conditions_str = json.dumps(session.assigned_conditions, ensure_ascii=False)
            
            writer.writerow([
                experiment_id,
                session.session_id,
                session.participant_code or '',
                session.experiment_group or '',
                session.condition_id or '',
                assigned_conditions_str,
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
                                          message_store: MessageStore = None,
                                          experiment_manager: Optional[ExperimentManager] = None,
                                          excel_format: bool = False,
                                          missing_value: str = 'blank') -> str:
        """
        実験データをワイド形式CSVでエクスポート（統計分析用）
        1行 = 1参加者（1セッション）
        各質問（question_id）が列になる
        
        【出力される列】
        1. 基本情報（16列）：
           - experiment_id, session_id, participant_code, client_id
           - condition_id, experiment_group, started_at, ended_at, duration_seconds
           - total_messages, user_message_count, bot_message_count
           - total_user_chars, total_user_words, avg_user_chars, avg_user_words
        
        2. ブランチ条件（実験設計による）：
           - {step_id}_condition: ブランチID（例: "branch_empathy"）
           - {step_id}_condition_label: ブランチラベル（例: "共感条件"）
           - {step_id}_condition_value: 条件値・数値コード（例: "1", "2"）
        
        3. チャット情報（各チャットステップごと）：
           - {step_id}_ai_model: 使用されたAIモデル
           - {step_id}_bot_name: ボット名
           - {step_id}_chat_duration_seconds: チャット時間（秒）
        
        4. 質問順序情報（ランダマイズされている場合）：
           - {step_id}_question_order: 提示された質問IDのリスト（カンマ区切り）
        
        5. アンケート回答：
           - 各question_idが列になる（panas_pre_1_strong, panas_post_1_strong, ...）
        
        6. AI評価結果：
           - ai_eval_{評価項目}: 評価スコア
        
        【欠損値の扱い】
        - 欠損値は空文字列として出力されます
        - Rでの読み込み時は na.strings=c("", "NA") を指定してください
        - 詳細は DATA_ANALYSIS_GUIDE.md を参照
        
        【使用例】
        ```python
        exporter = DataExporter()
        csv_content = exporter.export_experiment_wide_format_csv(
            experiment_id="exp_20251119_095620",
            session_manager=session_manager,
            message_store=message_store,
            experiment_manager=experiment_manager
        )
        ```
        """
        # 実験に属する全セッションを取得（statusに関係なく全て）
        all_sessions = session_manager.get_all_sessions()
        exp_sessions = [s for s in all_sessions if s.experiment_id == experiment_id]
        
        if not exp_sessions:
            # セッションがない場合は空のCSVを返す
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['experiment_id', 'session_id', 'participant_code', 'status', 'message'])
            writer.writerow([experiment_id, '', '', 'no_data', 'No sessions found for this experiment'])
            return output.getvalue()
        
        # 実験フローを取得（チャットステップ情報の取得用）
        experiment = None
        experiment_flow = None
        experiment_flow_raw = None  # 元のJSONデータ（ブランチ情報を含む）
        if experiment_manager:
            experiment = experiment_manager.get_experiment(experiment_id)
            if experiment and experiment.experiment_flow:
                from ..models.condition import ExperimentStep
                experiment_flow = [ExperimentStep.from_dict(step) for step in experiment.experiment_flow]
                # 元のJSONデータも保持（ブランチ情報を含む）
                experiment_flow_raw = experiment.experiment_flow
        
        # すべてのquestion_idを収集（カラムヘッダー用）
        all_question_ids = OrderedDict()  # 出現順を保持
        all_ai_eval_ids = OrderedDict()   # AI評価質問ID
        all_branch_fields = OrderedDict()  # ブランチ選択フィールド
        all_chat_fields = OrderedDict()  # チャットステップ情報
        all_survey_steps = set()  # 質問順序情報が必要なステップID
        
        # チャットステップ情報を収集（実験フローから、再帰的に探索）
        def collect_chat_steps_from_dict(steps_dict, chat_steps_list):
            """実験フロー（辞書形式）からチャットステップを再帰的に収集"""
            for step_dict in steps_dict:
                if isinstance(step_dict, dict):
                    if step_dict.get('step_type') == 'chat':
                        chat_steps_list.append(step_dict)
                    elif step_dict.get('step_type') == 'branch':
                        # ブランチ内のステップも探索
                        branches = step_dict.get('branches', [])
                        for branch in branches:
                            branch_steps = branch.get('steps', [])
                            if branch_steps:
                                collect_chat_steps_from_dict(branch_steps, chat_steps_list)
        
        chat_steps_in_flow = []
        if experiment_flow_raw:
            collect_chat_steps_from_dict(experiment_flow_raw, chat_steps_in_flow)
            for step_dict in chat_steps_in_flow:
                # チャットステップの情報フィールドを追加
                step_id = step_dict.get('step_id', '')
                field_name = f"{step_id}_ai_model"
                if field_name not in all_chat_fields:
                    all_chat_fields[field_name] = True
                field_name = f"{step_id}_bot_name"
                if field_name not in all_chat_fields:
                    all_chat_fields[field_name] = True
                field_name = f"{step_id}_chat_duration_seconds"
                if field_name not in all_chat_fields:
                    all_chat_fields[field_name] = True
        
        for session in exp_sessions:
            # ブランチ選択結果をassigned_conditionsから収集
            if hasattr(session, 'assigned_conditions') and session.assigned_conditions:
                for branch_step_id, branch_id in session.assigned_conditions.items():
                    # ブランチIDの列
                    field_name = f"{branch_step_id}_condition"
                    if field_name not in all_branch_fields:
                        all_branch_fields[field_name] = True
                    # ブランチラベルの列
                    label_field = f"{branch_step_id}_condition_label"
                    if label_field not in all_branch_fields:
                        all_branch_fields[label_field] = True
                    # ブランチ値の列（数値コード）
                    value_field = f"{branch_step_id}_condition_value"
                    if value_field not in all_branch_fields:
                        all_branch_fields[value_field] = True
            
            # 🆕 新形式: step_responsesからアンケート回答を収集
            if hasattr(session, 'step_responses') and session.step_responses:
                for step_id, step_data in session.step_responses.items():
                    if isinstance(step_data, dict):
                        for client_id, client_data in step_data.items():
                            if isinstance(client_data, dict):
                                # アンケート回答
                                if 'survey_responses' in client_data:
                                    all_survey_steps.add(step_id)  # 質問順序情報が必要
                                    for response in client_data['survey_responses']:
                                        if isinstance(response, dict) and 'question_id' in response:
                                            if response['question_id'] not in all_question_ids:
                                                all_question_ids[response['question_id']] = True
                                # ランダマイザーの回答（randomizer_responses内）
                                if 'randomizer_responses' in client_data:
                                    all_survey_steps.add(step_id)  # 質問順序情報が必要
                                    for response in client_data['randomizer_responses']:
                                        if isinstance(response, dict) and 'question_id' in response:
                                            if response['question_id'] not in all_question_ids:
                                                all_question_ids[response['question_id']] = True
                                # AI評価結果
                                if 'evaluation_results' in client_data:
                                    eval_results = client_data['evaluation_results']
                                    if isinstance(eval_results, dict):
                                        for eval_q_id in eval_results.keys():
                                            full_id = f"ai_eval_{eval_q_id}"
                                            if full_id not in all_ai_eval_ids:
                                                all_ai_eval_ids[full_id] = True
                                # ブランチ選択結果（後方互換性）
                                if 'branch_selected' in client_data:
                                    field_name = f"{step_id}_branch_selected"
                                    if field_name not in all_branch_fields:
                                        all_branch_fields[field_name] = True
                                if 'condition_label' in client_data:
                                    field_name = f"{step_id}_condition_label"
                                    if field_name not in all_branch_fields:
                                        all_branch_fields[field_name] = True
                                if 'condition_value' in client_data:
                                    field_name = f"{step_id}_condition_value"
                                    if field_name not in all_branch_fields:
                                        all_branch_fields[field_name] = True
            
            # 旧形式: survey_responses（後方互換性のため）
            if hasattr(session, 'survey_responses') and session.survey_responses:
                for client_id, responses in session.survey_responses.items():
                    for response in responses:
                        if hasattr(response, 'question_id'):
                            if response.question_id not in all_question_ids:
                                all_question_ids[response.question_id] = True
        
        # ヘッダー行を構築
        headers = [
            'experiment_id',
            'session_id',
            'participant_code',
            'client_id',
            'condition_id',
            'experiment_group',
            'status',                # セッションステータス（completed, active など）
            'flow_completed',        # フローが最後まで完了したか（TRUE/FALSE）
            'completed_steps_count', # 完了したステップ数
            'started_at',
            'ended_at',
            'duration_seconds',
            'total_messages',
            'user_message_count',
            'bot_message_count',
            'total_user_chars',      # ユーザーメッセージの総文字数
            'total_user_words',      # ユーザーメッセージの総単語数
            'avg_user_chars',
            'avg_user_words'
        ]
        
        # ブランチ選択列を追加（IDとラベルの両方）
        headers.extend(list(all_branch_fields.keys()))
        
        # チャットステップ情報列を追加
        headers.extend(list(all_chat_fields.keys()))
        
        # 質問順序情報の列を追加
        question_order_fields = [f"{step_id}_question_order" for step_id in sorted(all_survey_steps)]
        headers.extend(question_order_fields)
        
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
                # 'user'と'message'の両方をユーザーメッセージとして扱う
                user_messages = [m for m in messages if m.message_type in ['user', 'message']]
                bot_messages = [m for m in messages if m.message_type == 'bot']
                
                user_msg_count = len(user_messages)
                bot_msg_count = len(bot_messages)
                
                for msg in user_messages:
                    total_user_chars += msg.metadata.char_count
                    total_user_words += msg.metadata.word_count
            
            avg_user_chars = f"{total_user_chars / user_msg_count:.2f}" if user_msg_count > 0 else ''
            avg_user_words = f"{total_user_words / user_msg_count:.2f}" if user_msg_count > 0 else ''
            
            # client_idを取得（session.client_idを優先、なければparticipantsから）
            client_id = session.client_id if hasattr(session, 'client_id') and session.client_id else (session.participants[0] if session.participants else '')
            
            # セッション情報を計算
            completed_steps_count = len(session.completed_steps) if hasattr(session, 'completed_steps') and session.completed_steps else 0
            # フロー完了判定（実験フローがある場合、全ステップ完了しているか）
            flow_completed = ''
            if experiment_flow_raw:
                # フローのトップレベルステップ数（ブランチ内は個別にカウントされる）
                # completed_steps にはブランチ内のステップも含まれるため、
                # 最後のステップが完了していればフロー完了とみなす
                if hasattr(session, 'flow_completed') and session.flow_completed is not None:
                    flow_completed = 'TRUE' if session.flow_completed else 'FALSE'
                elif session.status == 'completed':
                    flow_completed = 'TRUE'
                elif completed_steps_count > 0:
                    flow_completed = 'FALSE'
            
            # 行データの基本部分
            row_data = [
                experiment_id,
                session.session_id,
                session.participant_code or '',
                client_id,
                session.condition_id or '',
                session.experiment_group or '',
                session.status or '',
                flow_completed,
                completed_steps_count,
                session.created_at,
                session.ended_at or '',
                duration_seconds,
                session.total_messages,
                user_msg_count,
                bot_msg_count,
                total_user_chars,
                total_user_words,
                avg_user_chars,
                avg_user_words
            ]
            
            # サーベイ回答を追加（question_idの順番に従って）
            survey_answers = {}
            
            # 🆕 新形式: step_responsesからアンケート回答を取得
            if hasattr(session, 'step_responses') and session.step_responses:
                for step_id, step_data in session.step_responses.items():
                    if isinstance(step_data, dict):
                        for client_id_resp, client_data in step_data.items():
                            if isinstance(client_data, dict):
                                # 通常のアンケート回答
                                if 'survey_responses' in client_data:
                                    for response in client_data['survey_responses']:
                                        if isinstance(response, dict) and 'question_id' in response:
                                            # 配列回答はJSON文字列に変換、文字列回答は改行を置換
                                            answer = response.get('answer')
                                            if isinstance(answer, list):
                                                answer = json.dumps(answer, ensure_ascii=False)
                                            elif isinstance(answer, str):
                                                # 改行をスペースに置換（CSVの行分割を防ぐ）
                                                answer = answer.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
                                            survey_answers[response['question_id']] = answer
                                # ランダマイザーの回答
                                if 'randomizer_responses' in client_data:
                                    for response in client_data['randomizer_responses']:
                                        if isinstance(response, dict) and 'question_id' in response:
                                            # 配列回答はJSON文字列に変換、文字列回答は改行を置換
                                            answer = response.get('answer')
                                            if isinstance(answer, list):
                                                answer = json.dumps(answer, ensure_ascii=False)
                                            elif isinstance(answer, str):
                                                # 改行をスペースに置換（CSVの行分割を防ぐ）
                                                answer = answer.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
                                            survey_answers[response['question_id']] = answer
            
            # 旧形式: survey_responses（後方互換性のため）
            if hasattr(session, 'survey_responses') and session.survey_responses:
                for client_id_resp, responses in session.survey_responses.items():
                    for response in responses:
                        if hasattr(response, 'question_id') and hasattr(response, 'answer'):
                            # 配列回答はJSON文字列に変換、文字列回答は改行を置換
                            answer = response.answer
                            if isinstance(answer, list):
                                answer = json.dumps(answer, ensure_ascii=False)
                            elif isinstance(answer, str):
                                # 改行をスペースに置換（CSVの行分割を防ぐ）
                                answer = answer.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
                            survey_answers[response.question_id] = answer
            
            # ブランチ選択結果を追加（ID、ラベル、値の3種類）
            branch_answers = {}
            
            # 実験フローからブランチ情報を取得するヘルパー関数
            def get_branch_info_from_flow(branch_step_id, branch_id):
                """実験フローから指定されたbranch_idのラベルと値を取得"""
                if not experiment_flow_raw:
                    return '', ''
                for step_dict in experiment_flow_raw:
                    if isinstance(step_dict, dict) and step_dict.get('step_id') == branch_step_id:
                        if step_dict.get('step_type') == 'branch':
                            branches = step_dict.get('branches', [])
                            for branch in branches:
                                if branch.get('branch_id') == branch_id:
                                    label = branch.get('condition_label', '')
                                    value = branch.get('condition_value', '')
                                    return label, value
                return '', ''
            
            # 新形式: assigned_conditionsから取得（優先）
            if hasattr(session, 'assigned_conditions') and session.assigned_conditions:
                for branch_step_id, branch_id in session.assigned_conditions.items():
                    # ブランチID
                    field_name = f"{branch_step_id}_condition"
                    branch_answers[field_name] = branch_id
                    # ブランチラベルと値（実験フローから取得）
                    label, value = get_branch_info_from_flow(branch_step_id, branch_id)
                    label_field = f"{branch_step_id}_condition_label"
                    branch_answers[label_field] = label
                    value_field = f"{branch_step_id}_condition_value"
                    branch_answers[value_field] = value
            
            # 旧形式: step_responsesから取得（後方互換性）
            if hasattr(session, 'step_responses') and session.step_responses:
                for step_id, step_data in session.step_responses.items():
                    if isinstance(step_data, dict):
                        for client_id_resp, client_data in step_data.items():
                            if isinstance(client_data, dict):
                                if 'branch_selected' in client_data:
                                    field_name = f"{step_id}_branch_selected"
                                    if field_name not in branch_answers:  # 新形式を優先
                                        branch_answers[field_name] = client_data['branch_selected']
                                if 'condition_label' in client_data:
                                    field_name = f"{step_id}_condition_label"
                                    if field_name not in branch_answers:  # 新形式を優先
                                        branch_answers[field_name] = client_data['condition_label']
                                if 'condition_value' in client_data:
                                    field_name = f"{step_id}_condition_value"
                                    if field_name not in branch_answers:  # 新形式を優先
                                        branch_answers[field_name] = client_data['condition_value']
            
            for field_name in all_branch_fields.keys():
                row_data.append(branch_answers.get(field_name, ''))
            
            # チャットステップ情報を追加
            chat_info = {}
            if experiment_flow_raw and message_store:
                # 完了したチャットステップを特定（ブランチ内も含めて再帰的に探索）
                def find_chat_step_by_id_from_dict(steps_dict, target_step_id):
                    """実験フロー（辞書形式）から指定されたstep_idのチャットステップを再帰的に検索"""
                    for step_dict in steps_dict:
                        if isinstance(step_dict, dict):
                            if step_dict.get('step_id') == target_step_id and step_dict.get('step_type') == 'chat':
                                return step_dict
                            elif step_dict.get('step_type') == 'branch':
                                # ブランチ内のステップも探索
                                branches = step_dict.get('branches', [])
                                for branch in branches:
                                    branch_steps = branch.get('steps', [])
                                    if branch_steps:
                                        found = find_chat_step_by_id_from_dict(branch_steps, target_step_id)
                                        if found:
                                            return found
                    return None
                
                completed_chat_steps = []
                if hasattr(session, 'completed_steps'):
                    for step_id in session.completed_steps:
                        # 実験フローからチャットステップを再帰的に検索
                        found_step = find_chat_step_by_id_from_dict(experiment_flow_raw, step_id)
                        if found_step:
                            completed_chat_steps.append(found_step)
                
                # 各チャットステップの情報を取得
                for step_dict in completed_chat_steps:
                    step_id = step_dict.get('step_id', '')
                    # AIモデルとbot_name
                    chat_info[f"{step_id}_ai_model"] = step_dict.get('bot_model', '')
                    chat_info[f"{step_id}_bot_name"] = step_dict.get('bot_name', '')
                    
                    # チャット時間を計算（メッセージから）
                    messages = message_store.get_messages_by_session(session.session_id)
                    chat_messages = [m for m in messages if m.message_type in ['user', 'bot']]
                    if chat_messages:
                        try:
                            start_time = datetime.fromisoformat(chat_messages[0].timestamp.replace('Z', '+00:00'))
                            end_time = datetime.fromisoformat(chat_messages[-1].timestamp.replace('Z', '+00:00'))
                            duration = int((end_time - start_time).total_seconds())
                            chat_info[f"{step_id}_chat_duration_seconds"] = duration
                        except:
                            chat_info[f"{step_id}_chat_duration_seconds"] = ''
                    else:
                        chat_info[f"{step_id}_chat_duration_seconds"] = ''
            
            for field_name in all_chat_fields.keys():
                row_data.append(chat_info.get(field_name, ''))
            
            # 質問順序情報を追加
            question_order_data = {}
            if hasattr(session, 'step_responses') and session.step_responses:
                for step_id, step_data in session.step_responses.items():
                    if isinstance(step_data, dict):
                        for client_id_resp, client_data in step_data.items():
                            if isinstance(client_data, dict):
                                # question_orderフィールドがある場合
                                if 'question_order' in client_data:
                                    order_list = client_data['question_order']
                                    if isinstance(order_list, list):
                                        # リストをカンマ区切りの文字列に変換
                                        question_order_data[f"{step_id}_question_order"] = ','.join(order_list)
            
            for field_name in question_order_fields:
                row_data.append(question_order_data.get(field_name, ''))
            
            # サーベイ回答を追加
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
            
            # 欠損値処理: 指定されたスタイルで欠損値を表現
            # missing_value: 'blank'=空文字列, 'NA'=NA文字列, 'comma'=空セル
            missing_val = self._get_missing_value(missing_value)
            row_data = [missing_val if (cell is None or cell == '') else cell for cell in row_data]
            
            writer.writerow(row_data)
        
        return self._add_bom_if_excel(output.getvalue(), excel_format)
    
    def export_experiment_wide_format_with_codebook(self, experiment_id: str, 
                                                     session_manager: SessionManager,
                                                     message_store: MessageStore = None,
                                                     experiment_manager: Optional[ExperimentManager] = None,
                                                     excel_format: bool = False,
                                                     missing_value: str = 'blank') -> bytes:
        """
        実験データをワイド形式CSVとコードブックCSVをZIPでエクスポート
        - データCSV: 全てのカテゴリカル変数を数値コードで出力
        - コードブックCSV: 変数名、値、ラベルの対応表
        
        Returns:
            bytes: ZIPファイルのバイナリデータ
        """
        # 実験に属する全セッションを取得
        all_sessions = session_manager.get_all_sessions()
        exp_sessions = [s for s in all_sessions if s.experiment_id == experiment_id]
        
        # 実験フローを取得
        experiment = None
        experiment_flow_raw = None
        if experiment_manager:
            experiment = experiment_manager.get_experiment(experiment_id)
            if experiment and experiment.experiment_flow:
                experiment_flow_raw = experiment.experiment_flow
        
        # コードブック用のマッピングを収集
        codebook_entries = []  # [(variable, value, label), ...]
        
        # ブランチ条件のコードブックを生成
        branch_code_map = {}  # {step_id: {branch_id: (value, label)}}
        
        # カテゴリカル変数のマッピング（実験フローから動的に取得）
        categorical_maps = {}  # {question_id: {label: value}}
        
        # 再帰的に実験フローからステップを収集する関数
        def collect_steps_from_flow(steps_list, collected_steps):
            for step_dict in steps_list:
                if isinstance(step_dict, dict):
                    collected_steps.append(step_dict)
                    # ブランチの場合は内部のステップも収集
                    if step_dict.get('step_type') == 'branch':
                        for branch in step_dict.get('branches', []):
                            branch_steps = branch.get('steps', [])
                            if branch_steps:
                                collect_steps_from_flow(branch_steps, collected_steps)
        
        all_steps = []
        if experiment_flow_raw:
            collect_steps_from_flow(experiment_flow_raw, all_steps)
        
        # 各ステップを処理
        for step_dict in all_steps:
            step_type = step_dict.get('step_type', '')
            
            # ブランチステップの処理
            if step_type == 'branch':
                step_id = step_dict.get('step_id', '')
                branches = step_dict.get('branches', [])
                branch_code_map[step_id] = {}
                for idx, branch in enumerate(branches, 1):
                    branch_id = branch.get('branch_id', '')
                    label = branch.get('condition_label', branch_id)
                    value = branch.get('condition_value', idx)
                    if value == '' or value is None:
                        value = idx
                    branch_code_map[step_id][branch_id] = (value, label)
                    codebook_entries.append((f"{step_id}_condition", value, label))
            
            # サーベイステップの処理（選択肢をコードブックに追加）
            elif step_type == 'survey':
                questions = step_dict.get('survey_questions', [])
                for q in questions:
                    q_id = q.get('question_id', '')
                    q_type = q.get('question_type', '')
                    options = q.get('options', [])
                    scale = q.get('scale')
                    
                    # radio/checkboxで選択肢がある場合
                    if q_type in ['radio', 'checkbox'] and options:
                        categorical_maps[q_id] = {}
                        for idx, opt in enumerate(options, 1):
                            categorical_maps[q_id][opt] = idx
                            codebook_entries.append((q_id, idx, opt))
                    
                    # likertスケールの場合
                    elif q_type == 'likert' and scale:
                        for i in range(1, scale + 1):
                            codebook_entries.append((q_id, i, f"Scale {i}/{scale}"))
        
        # flow_completed のコードブック
        codebook_entries.append(('flow_completed', 1, 'TRUE'))
        codebook_entries.append(('flow_completed', 0, 'FALSE'))
        
        # --- データCSVの生成（値のみ版） ---
        data_csv = self._generate_coded_data_csv(
            exp_sessions, experiment_id, experiment_flow_raw,
            branch_code_map, categorical_maps,
            message_store, missing_value, excel_format
        )
        
        # --- コードブックCSVの生成 ---
        codebook_csv = self._generate_codebook_csv(codebook_entries, excel_format)
        
        # --- ZIPファイルの生成 ---
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f'data_{experiment_id}.csv', data_csv)
            zf.writestr(f'codebook_{experiment_id}.csv', codebook_csv)
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
    
    def _generate_codebook_csv(self, codebook_entries: List[Tuple[str, Any, str]], 
                                excel_format: bool = False) -> str:
        """コードブックCSVを生成"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # ヘッダー
        writer.writerow(['variable', 'value', 'label'])
        
        # エントリを変数名でソートして出力
        sorted_entries = sorted(codebook_entries, key=lambda x: (x[0], x[1]))
        for variable, value, label in sorted_entries:
            writer.writerow([variable, value, label])
        
        return self._add_bom_if_excel(output.getvalue(), excel_format)
    
    def _generate_coded_data_csv(self, exp_sessions, experiment_id: str,
                                  experiment_flow_raw, branch_code_map: Dict,
                                  categorical_maps: Dict,
                                  message_store, missing_value: str,
                                  excel_format: bool = False) -> str:
        """全て数値コードに変換したデータCSVを生成"""
        if not exp_sessions:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['experiment_id', 'session_id', 'participant_code', 'status', 'message'])
            writer.writerow([experiment_id, '', '', 'no_data', 'No sessions found for this experiment'])
            return self._add_bom_if_excel(output.getvalue(), excel_format)
        
        # すべてのquestion_idを収集
        all_question_ids = OrderedDict()
        all_ai_eval_ids = OrderedDict()
        all_branch_step_ids = set()
        all_chat_fields = OrderedDict()
        all_survey_steps = set()
        
        # チャットステップ情報を収集
        def collect_chat_steps_from_dict(steps_dict, chat_steps_list):
            for step_dict in steps_dict:
                if isinstance(step_dict, dict):
                    if step_dict.get('step_type') == 'chat':
                        chat_steps_list.append(step_dict)
                    elif step_dict.get('step_type') == 'branch':
                        branches = step_dict.get('branches', [])
                        for branch in branches:
                            branch_steps = branch.get('steps', [])
                            if branch_steps:
                                collect_chat_steps_from_dict(branch_steps, chat_steps_list)
        
        chat_steps_in_flow = []
        if experiment_flow_raw:
            collect_chat_steps_from_dict(experiment_flow_raw, chat_steps_in_flow)
            for step_dict in chat_steps_in_flow:
                step_id = step_dict.get('step_id', '')
                all_chat_fields[f"{step_id}_ai_model"] = True
                all_chat_fields[f"{step_id}_bot_name"] = True
                all_chat_fields[f"{step_id}_chat_duration_seconds"] = True
            
            # ブランチステップIDを収集
            for step_dict in experiment_flow_raw:
                if isinstance(step_dict, dict) and step_dict.get('step_type') == 'branch':
                    all_branch_step_ids.add(step_dict.get('step_id', ''))
        
        for session in exp_sessions:
            # step_responsesからアンケート回答を収集
            if hasattr(session, 'step_responses') and session.step_responses:
                for step_id, step_data in session.step_responses.items():
                    if isinstance(step_data, dict):
                        for client_id, client_data in step_data.items():
                            if isinstance(client_data, dict):
                                if 'survey_responses' in client_data:
                                    all_survey_steps.add(step_id)
                                    for response in client_data['survey_responses']:
                                        if isinstance(response, dict) and 'question_id' in response:
                                            if response['question_id'] not in all_question_ids:
                                                all_question_ids[response['question_id']] = True
                                if 'randomizer_responses' in client_data:
                                    all_survey_steps.add(step_id)
                                    for response in client_data['randomizer_responses']:
                                        if isinstance(response, dict) and 'question_id' in response:
                                            if response['question_id'] not in all_question_ids:
                                                all_question_ids[response['question_id']] = True
                                if 'evaluation_results' in client_data:
                                    eval_results = client_data['evaluation_results']
                                    if isinstance(eval_results, dict):
                                        for eval_q_id in eval_results.keys():
                                            full_id = f"ai_eval_{eval_q_id}"
                                            if full_id not in all_ai_eval_ids:
                                                all_ai_eval_ids[full_id] = True
        
        # ヘッダー行を構築（ラベル列を除外、値列のみ）
        headers = [
            'experiment_id', 'session_id', 'participant_code', 'client_id',
            'condition_id', 'experiment_group', 'status', 'flow_completed',
            'completed_steps_count', 'started_at', 'ended_at', 'duration_seconds',
            'total_messages', 'user_message_count', 'bot_message_count',
            'total_user_chars', 'total_user_words', 'avg_user_chars', 'avg_user_words'
        ]
        
        # ブランチ条件列（値のみ）
        for step_id in sorted(all_branch_step_ids):
            headers.append(f"{step_id}_condition")
        
        # チャットステップ情報列
        headers.extend(list(all_chat_fields.keys()))
        
        # 質問順序情報の列
        question_order_fields = [f"{step_id}_question_order" for step_id in sorted(all_survey_steps)]
        headers.extend(question_order_fields)
        
        # サーベイ質問列
        headers.extend(list(all_question_ids.keys()))
        
        # AI評価列
        headers.extend(list(all_ai_eval_ids.keys()))
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        
        # 各セッションのデータを行として出力
        for session in exp_sessions:
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
                user_messages = [m for m in messages if m.message_type in ['user', 'message']]
                bot_messages = [m for m in messages if m.message_type == 'bot']
                user_msg_count = len(user_messages)
                bot_msg_count = len(bot_messages)
                for msg in user_messages:
                    total_user_chars += msg.metadata.char_count
                    total_user_words += msg.metadata.word_count
            
            avg_user_chars = f"{total_user_chars / user_msg_count:.2f}" if user_msg_count > 0 else ''
            avg_user_words = f"{total_user_words / user_msg_count:.2f}" if user_msg_count > 0 else ''
            
            client_id = session.client_id if hasattr(session, 'client_id') and session.client_id else (session.participants[0] if session.participants else '')
            completed_steps_count = len(session.completed_steps) if hasattr(session, 'completed_steps') and session.completed_steps else 0
            
            # flow_completedを数値コードに変換
            flow_completed = ''
            if hasattr(session, 'flow_completed') and session.flow_completed is not None:
                flow_completed = 1 if session.flow_completed else 0
            elif session.status == 'completed':
                flow_completed = 1
            elif completed_steps_count > 0:
                flow_completed = 0
            
            row_data = [
                experiment_id, session.session_id, session.participant_code or '', client_id,
                session.condition_id or '', session.experiment_group or '', session.status or '',
                flow_completed, completed_steps_count, session.created_at, session.ended_at or '',
                duration_seconds, session.total_messages, user_msg_count, bot_msg_count,
                total_user_chars, total_user_words, avg_user_chars, avg_user_words
            ]
            
            # ブランチ条件の値（数値コードのみ）
            for step_id in sorted(all_branch_step_ids):
                branch_value = ''
                if hasattr(session, 'assigned_conditions') and session.assigned_conditions:
                    branch_id = session.assigned_conditions.get(step_id, '')
                    if branch_id and step_id in branch_code_map:
                        if branch_id in branch_code_map[step_id]:
                            branch_value = branch_code_map[step_id][branch_id][0]  # 値のみ
                row_data.append(branch_value)
            
            # チャットステップ情報
            chat_info = {}
            if experiment_flow_raw and message_store:
                def find_chat_step_by_id_from_dict(steps_dict, target_step_id):
                    for step_dict in steps_dict:
                        if isinstance(step_dict, dict):
                            if step_dict.get('step_id') == target_step_id and step_dict.get('step_type') == 'chat':
                                return step_dict
                            elif step_dict.get('step_type') == 'branch':
                                for branch in step_dict.get('branches', []):
                                    found = find_chat_step_by_id_from_dict(branch.get('steps', []), target_step_id)
                                    if found:
                                        return found
                    return None
                
                completed_chat_steps = []
                if hasattr(session, 'completed_steps'):
                    for s_id in session.completed_steps:
                        found_step = find_chat_step_by_id_from_dict(experiment_flow_raw, s_id)
                        if found_step:
                            completed_chat_steps.append(found_step)
                
                for step_dict in completed_chat_steps:
                    s_id = step_dict.get('step_id', '')
                    chat_info[f"{s_id}_ai_model"] = step_dict.get('bot_model', '')
                    chat_info[f"{s_id}_bot_name"] = step_dict.get('bot_name', '')
                    messages = message_store.get_messages_by_session(session.session_id)
                    chat_messages = [m for m in messages if m.message_type in ['user', 'bot']]
                    if chat_messages:
                        try:
                            start_time = datetime.fromisoformat(chat_messages[0].timestamp.replace('Z', '+00:00'))
                            end_time = datetime.fromisoformat(chat_messages[-1].timestamp.replace('Z', '+00:00'))
                            chat_info[f"{s_id}_chat_duration_seconds"] = int((end_time - start_time).total_seconds())
                        except:
                            chat_info[f"{s_id}_chat_duration_seconds"] = ''
            
            for field_name in all_chat_fields.keys():
                row_data.append(chat_info.get(field_name, ''))
            
            # 質問順序情報
            question_order_data = {}
            if hasattr(session, 'step_responses') and session.step_responses:
                for step_id, step_data in session.step_responses.items():
                    if isinstance(step_data, dict):
                        for client_id_resp, client_data in step_data.items():
                            if isinstance(client_data, dict) and 'question_order' in client_data:
                                order_list = client_data['question_order']
                                if isinstance(order_list, list):
                                    question_order_data[f"{step_id}_question_order"] = ','.join(order_list)
            
            for field_name in question_order_fields:
                row_data.append(question_order_data.get(field_name, ''))
            
            # サーベイ回答（数値コード化）
            survey_answers = {}
            if hasattr(session, 'step_responses') and session.step_responses:
                for step_id, step_data in session.step_responses.items():
                    if isinstance(step_data, dict):
                        for client_id_resp, client_data in step_data.items():
                            if isinstance(client_data, dict):
                                for key in ['survey_responses', 'randomizer_responses']:
                                    if key in client_data:
                                        for response in client_data[key]:
                                            if isinstance(response, dict) and 'question_id' in response:
                                                answer = response.get('answer')
                                                q_id = response['question_id']
                                                # カテゴリカル変数を数値コード化
                                                if q_id in categorical_maps and isinstance(answer, str):
                                                    answer = categorical_maps[q_id].get(answer, answer)
                                                elif isinstance(answer, list):
                                                    answer = json.dumps(answer, ensure_ascii=False)
                                                elif isinstance(answer, str):
                                                    answer = answer.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
                                                survey_answers[q_id] = answer
            
            for q_id in all_question_ids.keys():
                row_data.append(survey_answers.get(q_id, ''))
            
            # AI評価結果
            ai_eval_answers = {}
            if hasattr(session, 'step_responses') and session.step_responses:
                for step_id, step_data in session.step_responses.items():
                    if isinstance(step_data, dict):
                        for client_id_resp, client_data in step_data.items():
                            if isinstance(client_data, dict) and 'evaluation_results' in client_data:
                                eval_results = client_data['evaluation_results']
                                if isinstance(eval_results, dict):
                                    for eval_q_id, score in eval_results.items():
                                        ai_eval_answers[f"ai_eval_{eval_q_id}"] = str(score)
            
            for eval_id in all_ai_eval_ids.keys():
                row_data.append(ai_eval_answers.get(eval_id, ''))
            
            # 欠損値処理
            missing_val = self._get_missing_value(missing_value)
            row_data = [missing_val if (cell is None or cell == '') else cell for cell in row_data]
            
            writer.writerow(row_data)
        
        return self._add_bom_if_excel(output.getvalue(), excel_format)

