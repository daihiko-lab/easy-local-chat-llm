from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import json


class ExperimentGroup(BaseModel):
    """実験グループモデル"""
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

