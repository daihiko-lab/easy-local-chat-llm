from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import json


class SurveyQuestion(BaseModel):
    """アンケート質問項目"""
    model_config = ConfigDict(extra='ignore')
    
    question_id: str  # 質問ID（例: "q1", "q2"）
    question_text: str  # 質問文
    question_type: str  # 質問タイプ: "likert", "text", "single_choice", "multiple_choice"
    required: bool = True  # 必須回答かどうか
    
    # リッカート尺度用の設定
    scale: Optional[int] = None  # 尺度のポイント数（例: 5 or 7）
    scale_min: Optional[int] = None  # 最小値（例: 1）
    scale_max: Optional[int] = None  # 最大値（例: 5 or 7）
    scale_min_label: Optional[str] = None  # 最小値のラベル（例: "全く当てはまらない"）
    scale_max_label: Optional[str] = None  # 最大値のラベル（例: "非常に当てはまる"）
    scale_labels: Optional[List[str]] = None  # 各ポイントのラベル（後方互換性のため）
    min_label: Optional[str] = None  # 最小値のラベル（後方互換性のため、scale_min_labelのエイリアス）
    max_label: Optional[str] = None  # 最大値のラベル（後方互換性のため、scale_max_labelのエイリアス）
    
    # 選択肢用の設定
    choices: Optional[List[str]] = None  # 選択肢リスト（旧形式）
    options: Optional[List[str]] = None  # 選択肢リスト（新形式、choicesのエイリアス）
    
    # 自由記述用の設定
    input_type: Optional[str] = None  # 入力タイプ（"text", "number", "email"等）
    placeholder: Optional[str] = None  # プレースホルダーテキスト
    max_length: Optional[int] = None  # 最大文字数
    
    def to_dict(self):
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class ExperimentStep(BaseModel):
    """実験フローの各ステップ"""
    model_config = ConfigDict(extra='ignore')
    
    step_id: str  # ステップID（例: "step1", "consent", "pre_survey"）
    step_type: str  # ステップタイプ: "consent", "instruction", "survey", "chat", "debriefing"
    title: Optional[str] = None  # ステップのタイトル
    
    # 同意書・教示文・デブリーフィング用
    content: Optional[str] = None  # 表示するテキスト内容
    
    # インストラクション用タイマー設定
    min_display_seconds: Optional[int] = None  # 最小表示時間（秒）
    show_timer: Optional[bool] = None  # タイマーを表示するか（None=デフォルト動作）
    
    # アンケート用
    survey_questions: Optional[List[SurveyQuestion]] = None  # 質問リスト
    survey_description: Optional[str] = None  # アンケート説明文
    randomize_questions: Optional[bool] = None  # 質問順序をランダム化
    
    # チャット用
    time_limit_minutes: Optional[int] = None  # チャット時間制限（分）
    bot_model: Optional[str] = None  # AIモデル名（例: "gemma3:4b"）
    bot_name: Optional[str] = None  # ボット名（例: "カウンセラーAI"）
    system_prompt: Optional[str] = None  # システムプロンプト
    instruction_text: Optional[str] = None  # チャット開始時の教示文
    temperature: Optional[float] = 0.7  # AI応答の温度パラメータ（0.0〜2.0、デフォルト0.7）
    top_p: Optional[float] = 0.9  # Nucleus samplingパラメータ（0.0〜1.0、デフォルト0.9）
    top_k: Optional[int] = 40  # Top-k samplingパラメータ（整数、デフォルト40）
    repeat_penalty: Optional[float] = 1.1  # 繰り返しペナルティ（1.0〜2.0、デフォルト1.1）
    num_predict: Optional[int] = None  # 最大生成トークン数（Noneで制限なし）
    num_thread: Optional[int] = None  # CPUスレッド数（Noneでデフォルト: 8）
    num_ctx: Optional[int] = None  # コンテキスト長（Noneでデフォルト: 8192）
    num_gpu: Optional[int] = None  # GPUレイヤー数（Noneでデフォルト: -1、全レイヤー）
    num_batch: Optional[int] = None  # バッチサイズ（Noneでデフォルト: 512）
    
    # AI評価用
    evaluation_model: Optional[str] = None  # AI評価用のモデル名
    evaluation_questions: Optional[List[SurveyQuestion]] = None  # AI評価用の質問リスト
    context_prompt: Optional[str] = None  # AI評価用のコンテキストプロンプト
    
    # ブランチ用
    branches: Optional[List[Dict[str, Any]]] = None  # ブランチのリスト（各ブランチにbranch_id, condition_label, condition_type, condition_value, weight, stepsが含まれる）
    
    # ランダマイザー用
    steps: Optional[List[Dict[str, Any]]] = None  # ランダマイザー内のステップリスト（survey_randomizer用）
    surveys: Optional[List[Dict[str, Any]]] = None  # ランダマイザー内のサーベイリスト（後方互換性のため）
    
    # ボタンテキストのカスタマイズ
    button_text: Optional[str] = None  # 次へ進むボタンのテキスト（例: "同意する", "次へ", "送信"）
    
    # 必須ステップかどうか
    required: bool = True  # Falseの場合スキップ可能
    
    def to_dict(self):
        data = self.model_dump()
        # survey_questionsをシリアライズ
        if self.survey_questions:
            data['survey_questions'] = [q.to_dict() for q in self.survey_questions]
        # evaluation_questionsをシリアライズ
        if self.evaluation_questions:
            data['evaluation_questions'] = [q.to_dict() for q in self.evaluation_questions]
        return data
    
    @classmethod
    def from_dict(cls, data: dict):
        # survey_questionsをデシリアライズ
        if 'survey_questions' in data and data['survey_questions']:
            data['survey_questions'] = [SurveyQuestion.from_dict(q) for q in data['survey_questions']]
        # evaluation_questionsをデシリアライズ
        if 'evaluation_questions' in data and data['evaluation_questions']:
            data['evaluation_questions'] = [SurveyQuestion.from_dict(q) for q in data['evaluation_questions']]
        return cls(**data)


class Condition(BaseModel):
    """実験条件（Condition）モデル"""
    model_config = ConfigDict(extra='ignore')
    
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
    
    # 🆕 多段階実験フロー（汎用的な設計）
    experiment_flow: Optional[List[ExperimentStep]] = None  # 実験フローの定義
    
    # 🔻 旧形式（後方互換性のため残す、experiment_flowが優先）
    instruction_text: Optional[str] = None  # 参加者への教示文（想起ステップ）
    time_limit_minutes: Optional[int] = None  # タイムリミット（分）
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
        # survey_questionsをシリアライズ（旧形式）
        if self.survey_questions:
            data['survey_questions'] = [q.to_dict() for q in self.survey_questions]
        # experiment_flowをシリアライズ（新形式）
        if self.experiment_flow:
            data['experiment_flow'] = [step.to_dict() for step in self.experiment_flow]
        return data
    
    def to_json(self):
        """JSON文字列に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict):
        """辞書からインスタンスを作成"""
        # survey_questionsをデシリアライズ（旧形式）
        if 'survey_questions' in data and data['survey_questions']:
            data['survey_questions'] = [SurveyQuestion.from_dict(q) for q in data['survey_questions']]
        # experiment_flowをデシリアライズ（新形式）
        if 'experiment_flow' in data and data['experiment_flow']:
            data['experiment_flow'] = [ExperimentStep.from_dict(step) for step in data['experiment_flow']]
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str):
        """JSON文字列からインスタンスを作成"""
        return cls.from_dict(json.loads(json_str))
    
    def get_effective_flow(self) -> Optional[List[ExperimentStep]]:
        """
        有効な実験フローを取得
        experiment_flowが設定されていればそれを返す
        なければ旧形式から自動生成
        """
        if self.experiment_flow:
            return self.experiment_flow
        
        # 旧形式から自動生成
        return self._convert_legacy_to_flow()
    
    def _convert_legacy_to_flow(self) -> Optional[List[ExperimentStep]]:
        """旧形式のフィールドをフローに変換"""
        steps = []
        
        # 教示文があればinstructionステップとして追加
        if self.instruction_text:
            steps.append(ExperimentStep(
                step_id="instruction",
                step_type="instruction",
                title="実験の説明",
                content=self.instruction_text,
                button_text="開始する",
                required=True
            ))
        
        # チャットステップを追加
        steps.append(ExperimentStep(
            step_id="chat",
            step_type="chat",
            time_limit_minutes=self.time_limit_minutes,
            required=True
        ))
        
        # アンケートがあればsurveyステップとして追加
        if self.survey_questions:
            steps.append(ExperimentStep(
                step_id="survey",
                step_type="survey",
                title=self.survey_title or "アンケート",
                survey_description=self.survey_description,
                survey_questions=self.survey_questions,
                button_text="送信",
                required=True
            ))
        
        return steps if steps else None

