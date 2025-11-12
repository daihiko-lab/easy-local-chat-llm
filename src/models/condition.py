from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import json


class SurveyQuestion(BaseModel):
    """アンケート質問項目"""
    question_id: str  # 質問ID（例: "q1", "q2"）
    question_text: str  # 質問文
    question_type: str  # 質問タイプ: "likert", "text", "single_choice", "multiple_choice"
    required: bool = True  # 必須回答かどうか
    
    # リッカート尺度用の設定
    scale_min: Optional[int] = None  # 最小値（例: 1）
    scale_max: Optional[int] = None  # 最大値（例: 5 or 7）
    scale_min_label: Optional[str] = None  # 最小値のラベル（例: "全く当てはまらない"）
    scale_max_label: Optional[str] = None  # 最大値のラベル（例: "非常に当てはまる"）
    
    # 選択肢用の設定
    choices: Optional[List[str]] = None  # 選択肢リスト
    
    # 自由記述用の設定
    max_length: Optional[int] = None  # 最大文字数
    
    def to_dict(self):
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


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
    
    # 実験デザイン
    instruction_text: Optional[str] = None  # 参加者への教示文
    time_limit_minutes: Optional[int] = None  # タイムリミット（分）
    
    # アンケート設定
    survey_questions: Optional[List[SurveyQuestion]] = None  # アンケート質問リスト
    survey_title: Optional[str] = None  # アンケートタイトル
    survey_description: Optional[str] = None  # アンケート説明文
    
    # メタデータ
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    is_active: bool = True
    
    def to_dict(self):
        """辞書形式に変換"""
        data = self.model_dump()
        # survey_questionsをシリアライズ
        if self.survey_questions:
            data['survey_questions'] = [q.to_dict() for q in self.survey_questions]
        return data
    
    def to_json(self):
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict):
        """辞書からインスタンスを作成"""
        # survey_questionsをデシリアライズ
        if 'survey_questions' in data and data['survey_questions']:
            data['survey_questions'] = [SurveyQuestion.from_dict(q) for q in data['survey_questions']]
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str):
        """JSON文字列からインスタンスを作成"""
        return cls.from_dict(json.loads(json_str))

