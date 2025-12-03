from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import json


class SessionMetadata(BaseModel):
    """セッションのメタデータ"""
    model_config = ConfigDict(extra='ignore')
    
    purpose: Optional[str] = None  # 実験の目的など
    notes: Optional[str] = None    # メモ


class SurveyResponse(BaseModel):
    """アンケート回答"""
    model_config = ConfigDict(extra='ignore')
    
    question_id: str  # 質問ID
    answer: Any  # 回答（質問タイプによって型が異なる）
    answered_at: str = Field(default_factory=lambda: datetime.now().isoformat())  # 回答時刻
    
    def to_dict(self):
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class Session(BaseModel):
    """チャットセッションモデル"""
    model_config = ConfigDict(extra='ignore')
    
    session_id: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    ended_at: Optional[str] = None
    # 状態: active(進行中), paused(一時停止), completed(正常完了), 
    #       cancelled(管理者によるキャンセル), abandoned(参加者離脱), ended(終了/旧形式互換)
    status: str = "active"
    participants: List[str] = Field(default_factory=list)
    
    # 状態変更履歴
    status_history: List[Dict[str, Any]] = Field(default_factory=list)  # [{status, changed_at, changed_by, note}]
    total_messages: int = 0
    last_activity: str = Field(default_factory=lambda: datetime.now().isoformat())  # 最終アクティビティ時刻
    metadata: SessionMetadata = Field(default_factory=SessionMetadata)
    
    # 実験トラッキング
    experiment_id: Optional[str] = None  # 所属する実験ID
    condition_id: Optional[str] = None  # 使用された条件ID
    experiment_group: Optional[str] = None  # 実験条件名（割り当てられた条件）
    participant_code: Optional[str] = None  # 🆕 参加者コード
    client_id: Optional[str] = None  # 🆕 クライアントID（表示・追跡用）
    
    # アンケート回答（参加者ごとに保存）
    survey_responses: Dict[str, List[SurveyResponse]] = Field(default_factory=dict)  # {client_id: [SurveyResponse, ...]}
    
    # 🆕 多段階実験フロー管理
    current_step_index: int = 0  # 現在のステップインデックス（0始まり）
    completed_steps: List[str] = Field(default_factory=list)  # 完了したステップのID一覧
    step_responses: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # {step_id: {client_id: response_data}}
    completed_participants: List[str] = Field(default_factory=list)  # 実験を完了した参加者のclient_id一覧
    assigned_conditions: Dict[str, str] = Field(default_factory=dict)  # ブランチポイント -> 割り当てられた条件ラベル
    
    def add_participant(self, client_id: str):
        """参加者を追加"""
        if client_id not in self.participants:
            self.participants.append(client_id)
            self.update_activity()
    
    def remove_participant(self, client_id: str):
        """参加者を削除"""
        if client_id in self.participants:
            self.participants.remove(client_id)
            self.update_activity()
    
    def increment_message_count(self):
        """メッセージ数をインクリメント"""
        self.total_messages += 1
        self.update_activity()
    
    def update_activity(self):
        """最終アクティビティ時刻を更新"""
        self.last_activity = datetime.now().isoformat()
    
    def get_idle_seconds(self) -> float:
        """最後のアクティビティからの経過秒数を取得"""
        try:
            last = datetime.fromisoformat(self.last_activity)
            return (datetime.now() - last).total_seconds()
        except (ValueError, AttributeError):
            # last_activity が設定されていない場合は0を返す
            return 0.0
    
    def get_idle_minutes(self) -> float:
        """最後のアクティビティからの経過分数を取得"""
        return self.get_idle_seconds() / 60.0
    
    def end_session(self):
        """セッションを終了"""
        self.change_status("ended", changed_by="system", note="Session ended")
    
    def change_status(self, new_status: str, changed_by: str = "system", note: str = ""):
        """セッション状態を変更（履歴付き）
        
        Args:
            new_status: 新しい状態 (active, paused, completed, cancelled, abandoned, ended)
            changed_by: 変更者 (admin, system, participant)
            note: 変更理由メモ
        """
        old_status = self.status
        if old_status == new_status:
            return
        
        self.status = new_status
        
        # 終了系の状態の場合、ended_atを設定
        if new_status in ["ended", "completed", "cancelled", "abandoned"]:
            self.ended_at = datetime.now().isoformat()
        elif new_status == "active" and self.ended_at:
            # アクティブに戻す場合、ended_atをクリア
            self.ended_at = None
        
        # 履歴に追加
        self.status_history.append({
            "old_status": old_status,
            "new_status": new_status,
            "changed_at": datetime.now().isoformat(),
            "changed_by": changed_by,
            "note": note
        })
        
        self.update_activity()
    
    def add_survey_response(self, client_id: str, responses: List[SurveyResponse]):
        """アンケート回答を追加"""
        self.survey_responses[client_id] = responses
        self.update_activity()
    
    def get_survey_response(self, client_id: str) -> Optional[List[SurveyResponse]]:
        """アンケート回答を取得"""
        return self.survey_responses.get(client_id)
    
    # 🆕 フロー管理メソッド
    def advance_step(self):
        """次のステップへ進む"""
        self.current_step_index += 1
        self.update_activity()
    
    def complete_step(self, step_id: str):
        """ステップを完了としてマーク"""
        if step_id not in self.completed_steps:
            self.completed_steps.append(step_id)
            self.update_activity()
    
    def add_step_response(self, step_id: str, client_id: str, response_data: Any):
        """ステップの回答を保存"""
        if step_id not in self.step_responses:
            self.step_responses[step_id] = {}
        self.step_responses[step_id][client_id] = response_data
        self.update_activity()
    
    def mark_participant_completed(self, client_id: str):
        """参加者を実験完了としてマーク"""
        if client_id not in self.completed_participants:
            self.completed_participants.append(client_id)
            self.update_activity()
    
    def is_participant_completed(self, client_id: str) -> bool:
        """参加者が実験を完了済みかチェック"""
        return client_id in self.completed_participants
    
    def get_step_response(self, step_id: str, client_id: str) -> Optional[Any]:
        """ステップの回答を取得"""
        return self.step_responses.get(step_id, {}).get(client_id)
    
    def assign_condition(self, branch_id: str, condition_label: str):
        """ブランチポイントで割り当てられた条件を記録"""
        self.assigned_conditions[branch_id] = condition_label
        self.update_activity()
    
    def get_assigned_condition(self, branch_id: str) -> Optional[str]:
        """ブランチポイントで割り当てられた条件を取得"""
        return self.assigned_conditions.get(branch_id)
    
    def to_dict(self):
        """辞書形式に変換"""
        data = self.model_dump()
        # survey_responsesをシリアライズ
        if self.survey_responses:
            data['survey_responses'] = {
                client_id: [resp.to_dict() for resp in responses]
                for client_id, responses in self.survey_responses.items()
            }
        return data
    
    def to_json(self):
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict):
        """辞書からインスタンスを作成"""
        # survey_responsesをデシリアライズ
        if 'survey_responses' in data and data['survey_responses']:
            data['survey_responses'] = {
                client_id: [SurveyResponse.from_dict(resp) for resp in responses]
                for client_id, responses in data['survey_responses'].items()
            }
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str):
        """JSON文字列からインスタンスを作成"""
        return cls.from_dict(json.loads(json_str))

