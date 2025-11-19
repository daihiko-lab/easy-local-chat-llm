from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from pydantic import BaseModel, Field, ConfigDict
import json
import random
import string

# 循環importを避けるため
if TYPE_CHECKING:
    from .condition import ExperimentStep


class ExperimentGroup(BaseModel):
    """実験グループモデル"""
    model_config = ConfigDict(extra='ignore')
    
    experiment_id: str
    name: str = "New Experiment"
    slug: Optional[str] = None  # URLフレンドリーな名前
    description: Optional[str] = None
    researcher: Optional[str] = None  # 研究者名
    
    # タイムスタンプ
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    
    # ステータス
    status: str = "planning"  # planning | active | paused | completed
    
    # データディレクトリ
    data_directory: Optional[str] = None  # 例: data/experiments/20241029_143022
    
    # 関連するセッショングループ（テンプレート）のリスト
    template_ids: List[str] = Field(default_factory=list)
    
    # 参加者数とセッション数
    total_participants: int = 0
    total_sessions: int = 0
    
    # 同時セッション数制限（None = 無制限）
    max_concurrent_sessions: Optional[int] = None
    
    # 🆕 実験レベルの共通フロー（全条件で共有）
    experiment_flow: Optional[List[dict]] = None  # ExperimentStepのリスト（dict形式で保存）
    
    # 🆕 参加者コード管理
    participant_codes: dict = Field(default_factory=dict)  # {code: {"status": "unused|used|completed", "client_id": str, "session_id": str, "completed_at": str}}
    
    def get_experiment_flow_steps(self) -> Optional[List['ExperimentStep']]:
        """実験フローをExperimentStepオブジェクトのリストとして取得"""
        if not self.experiment_flow:
            return None
        
        from .condition import ExperimentStep
        return [ExperimentStep.from_dict(step) for step in self.experiment_flow]
    
    def generate_participant_codes(self, count: int, length: int = 6) -> List[dict]:
        """ランダムな参加者コードを生成"""
        codes = []
        chars = string.ascii_lowercase + string.digits  # a-z, 0-9
        # 混同しやすい文字を除外
        chars = chars.replace('o', '').replace('0', '').replace('i', '').replace('1', '').replace('l', '')
        
        for i in range(count):
            # 既存のコードと重複しないように生成
            while True:
                code = ''.join(random.choice(chars) for _ in range(length))
                if code not in self.participant_codes:
                    break
            
            # 各コードに固有の4桁PINを生成
            password = ''.join(random.choice(string.digits) for _ in range(4))
            
            self.participant_codes[code] = {
                "status": "unused",
                "password": password,
                "client_id": None,
                "session_id": None,
                "completed_at": None,
                "created_at": datetime.now().isoformat()
            }
            codes.append({"code": code, "password": password})
        
        return codes
    
    def is_code_valid(self, code: str) -> bool:
        """コードが有効（存在する）かチェック"""
        return code in self.participant_codes
    
    def is_code_available(self, code: str) -> bool:
        """コードが使用可能（未使用のみ）かチェック"""
        if code not in self.participant_codes:
            return False
        status = self.participant_codes[code]["status"]
        # unused のみ使用可能（used, completedはブロック）
        return status == "unused"
    
    def verify_code_password(self, code: str, password: str) -> bool:
        """コードとパスワードの組み合わせを検証"""
        if code not in self.participant_codes:
            return False
        stored_password = self.participant_codes[code].get("password")
        return stored_password == password
    
    def get_code_status(self, code: str) -> Optional[str]:
        """コードの状態を取得"""
        if code not in self.participant_codes:
            return None
        return self.participant_codes[code]["status"]
    
    def get_code_session(self, code: str) -> Optional[str]:
        """コードに紐付いたセッションIDを取得"""
        if code not in self.participant_codes:
            return None
        return self.participant_codes[code].get("session_id")
    
    def mark_code_used(self, code: str, client_id: str, session_id: str):
        """コードを使用済みにマーク"""
        if code in self.participant_codes:
            self.participant_codes[code]["status"] = "used"
            self.participant_codes[code]["client_id"] = client_id
            self.participant_codes[code]["session_id"] = session_id
    
    def mark_code_completed(self, code: str):
        """コードを完了済みにマーク"""
        if code in self.participant_codes:
            self.participant_codes[code]["status"] = "completed"
            self.participant_codes[code]["completed_at"] = datetime.now().isoformat()
    
    def to_dict(self):
        """辞書形式に変換"""
        return self.model_dump()
    
    def to_json(self):
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict):
        """辞書からインスタンスを作成"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str):
        """JSON文字列からインスタンスを作成"""
        return cls.from_dict(json.loads(json_str))

