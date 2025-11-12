from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json
import hashlib


class SessionMetadata(BaseModel):
    """セッションのメタデータ"""
    purpose: Optional[str] = None  # 実験の目的など
    notes: Optional[str] = None    # メモ


class SurveyResponse(BaseModel):
    """アンケート回答"""
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
    session_id: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    ended_at: Optional[str] = None
    status: str = "active"  # active | ended
    participants: List[str] = Field(default_factory=list)
    total_messages: int = 0
    last_activity: str = Field(default_factory=lambda: datetime.now().isoformat())  # 最終アクティビティ時刻
    metadata: SessionMetadata = Field(default_factory=SessionMetadata)
    password_protected: bool = False  # セッション全体のパスワード保護
    password_hash: Optional[str] = None  # セッションパスワードのハッシュ値
    user_passwords: dict = Field(default_factory=dict)  # ユーザーID別パスワード {client_id: password_hash}
    require_user_password: bool = False  # ユーザーパスワード必須（True=必須、False=任意）
    disable_user_password: bool = False  # ユーザーパスワード完全無効（True=パスワードなし強制）
    
    # 実験トラッキング
    experiment_id: Optional[str] = None  # 所属する実験ID
    condition_id: Optional[str] = None  # 使用された条件ID
    experiment_group: Optional[str] = None  # 実験条件名（割り当てられた条件）
    
    # アンケート回答（参加者ごとに保存）
    survey_responses: Dict[str, List[SurveyResponse]] = Field(default_factory=dict)  # {client_id: [SurveyResponse, ...]}
    
    @staticmethod
    def hash_password(password: str) -> str:
        """パスワードをハッシュ化"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def set_password(self, password: str):
        """パスワードを設定"""
        if password:
            self.password_protected = True
            self.password_hash = self.hash_password(password)
        else:
            self.password_protected = False
            self.password_hash = None
    
    def verify_password(self, password: str) -> bool:
        """セッションパスワードを検証"""
        if not self.password_protected:
            return True  # パスワード保護されていない場合は常にTrue
        if not password:
            return False
        return self.password_hash == self.hash_password(password)
    
    def set_user_password(self, client_id: str, password: str):
        """ユーザーIDにパスワードを設定"""
        if password:
            self.user_passwords[client_id] = self.hash_password(password)
    
    def has_user_password(self, client_id: str) -> bool:
        """ユーザーIDがパスワード保護されているか確認"""
        return client_id in self.user_passwords
    
    def verify_user_password(self, client_id: str, password: str) -> bool:
        """ユーザーIDのパスワードを検証"""
        if not self.has_user_password(client_id):
            return True  # パスワード保護されていない場合は常にTrue
        if not password:
            return False
        return self.user_passwords.get(client_id) == self.hash_password(password)
    
    def get_protected_users(self) -> List[str]:
        """パスワード保護されているユーザーIDのリストを取得"""
        return list(self.user_passwords.keys())
    
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
        self.status = "ended"
        self.ended_at = datetime.now().isoformat()
    
    def add_survey_response(self, client_id: str, responses: List[SurveyResponse]):
        """アンケート回答を追加"""
        self.survey_responses[client_id] = responses
        self.update_activity()
    
    def get_survey_response(self, client_id: str) -> Optional[List[SurveyResponse]]:
        """アンケート回答を取得"""
        return self.survey_responses.get(client_id)
    
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

