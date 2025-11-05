from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import json


class Condition(BaseModel):
    """実験条件（Condition）モデル"""
    condition_id: str
    name: str = "Default Condition"
    description: Optional[str] = None
    
    # ボット設定
    bot_model: str = "gemma3:4b"
    system_prompt: str = ""  # 空文字列可（オプション）
    
    # セッション設定
    auto_create_session: bool = True  # ログイン時に自動でセッション作成
    end_previous_session: bool = False  # 前回のセッションを自動終了（実験では通常False）
    
    # 実験設定
    is_experiment: bool = False  # 実験用条件かどうか
    experiment_group: Optional[str] = None  # 実験条件名（例: "条件A", "統制群"）
    weight: int = 1  # ランダム割り当て時の重み（デフォルト: 1 = 均等）
    
    # メタデータ
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True
    
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

