import json
import random
from typing import Optional, List, Tuple
from pathlib import Path
from datetime import datetime
from ..models.condition import Condition


class ConditionManager:
    """実験条件管理クラス"""
    
    def __init__(self, data_dir: str = None, condition_file: str = None):
        """
        初期化
        
        Args:
            data_dir: 条件を保存するディレクトリ（condition_fileが指定されていない場合）
            condition_file: 条件ファイルのフルパス（優先）
        """
        if condition_file:
            # ファイルパスが直接指定された場合
            self.condition_file = Path(condition_file)
            self.data_dir = self.condition_file.parent
        else:
            # ディレクトリが指定された場合
            self.data_dir = Path(data_dir or "data/conditions")
            self.condition_file = self.data_dir / "conditions.json"
        
        # ディレクトリを作成
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # デフォルト条件を初期化
        self._initialize_default_condition()
    
    def _initialize_default_condition(self):
        """デフォルト条件を作成"""
        if not self.condition_file.exists():
            default_condition = Condition(
                condition_id="default",
                name="デフォルト設定",
                description="標準的なチャットボット設定",
                bot_model="gemma3:4b",
                system_prompt="あなたは親切で役立つAIアシスタントです。ユーザーの質問に丁寧に答えてください。",
                auto_create_session=True,
                end_previous_session=True
            )
            self.save_condition(default_condition)
    
    def save_condition(self, condition: Condition):
        """条件を保存"""
        conditions = self.get_all_conditions()
        
        # 既存の条件を更新または追加
        condition.updated_at = datetime.now().isoformat()
        
        # 既存の条件を探して更新
        updated = False
        for i, c in enumerate(conditions):
            if c.condition_id == condition.condition_id:
                conditions[i] = condition
                updated = True
                break
        
        if not updated:
            conditions.append(condition)
        
        # ファイルに保存
        with open(self.condition_file, 'w', encoding='utf-8') as f:
            json.dump([c.to_dict() for c in conditions], f, ensure_ascii=False, indent=2)
    
    def get_condition(self, condition_id: str) -> Optional[Condition]:
        """条件を取得"""
        conditions = self.get_all_conditions()
        for condition in conditions:
            if condition.condition_id == condition_id:
                return condition
        return None
    
    def get_all_conditions(self) -> List[Condition]:
        """全条件を取得"""
        if not self.condition_file.exists():
            return []
        
        with open(self.condition_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                return [Condition.from_dict(c) for c in data]
            except json.JSONDecodeError:
                return []
    
    def get_active_condition(self) -> Optional[Condition]:
        """アクティブな条件を取得"""
        conditions = self.get_all_conditions()
        for condition in conditions:
            if condition.is_active:
                return condition
        return None
    
    def set_active_condition(self, condition_id: str):
        """条件をアクティブに設定"""
        conditions = self.get_all_conditions()
        
        for condition in conditions:
            condition.is_active = (condition.condition_id == condition_id)
            condition.updated_at = datetime.now().isoformat()
        
        # 保存
        with open(self.condition_file, 'w', encoding='utf-8') as f:
            json.dump([c.to_dict() for c in conditions], f, ensure_ascii=False, indent=2)
    
    def delete_condition(self, condition_id: str) -> bool:
        """条件を削除"""
        if condition_id == "default":
            return False  # デフォルト条件は削除不可
        
        conditions = self.get_all_conditions()
        conditions = [c for c in conditions if c.condition_id != condition_id]
        
        with open(self.condition_file, 'w', encoding='utf-8') as f:
            json.dump([c.to_dict() for c in conditions], f, ensure_ascii=False, indent=2)
        
        return True
    
    def get_experiment_conditions(self) -> List[Condition]:
        """実験用条件のみを取得"""
        conditions = self.get_all_conditions()
        return [c for c in conditions if c.is_experiment]
    
    def select_random_experiment_condition(self) -> Optional[Condition]:
        """実験用条件からランダムに1つ選択（重み付き）"""
        experiment_conditions = self.get_experiment_conditions()
        
        if not experiment_conditions:
            return None
        
        # 重み付きランダム選択
        weights = [c.weight for c in experiment_conditions]
        selected = random.choices(experiment_conditions, weights=weights, k=1)[0]
        
        return selected
    
    def create_session_from_condition(self, session_manager, experiment_manager=None, 
                                    condition_id: Optional[str] = None, 
                                    use_random_experiment: bool = False):
        """条件から新しいセッションを作成
        
        Args:
            session_manager: セッションマネージャー
            experiment_manager: 実験マネージャー（省略可）
            condition_id: 使用する条件ID（Noneの場合はアクティブ条件）
            use_random_experiment: True の場合、実験用条件からランダムに選択
        
        Returns:
            (session, condition) のタプル
        """
        if use_random_experiment:
            # 実験用条件からランダムに選択
            condition = self.select_random_experiment_condition()
            if not condition:
                # 実験用条件がない場合は通常のフロー
                condition = self.get_active_condition()
        elif condition_id:
            condition = self.get_condition(condition_id)
        else:
            condition = self.get_active_condition()
        
        if not condition:
            condition = self.get_condition("default")
        
        if not condition:
            raise ValueError("No condition found")
        
        # 前回のセッションを終了
        if condition.end_previous_session:
            active_sessions = session_manager.get_active_sessions()
            for session in active_sessions:
                session_manager.end_session(session.session_id)
        
        # 新しいセッションを作成
        new_session = session_manager.create_session()
        
        # セッションに条件情報を記録（実験条件の追跡用）
        new_session.condition_id = condition.condition_id
        new_session.experiment_group = condition.experiment_group if condition.is_experiment else None
        
        # アクティブな実験があれば実験IDを記録
        if experiment_manager:
            active_exp = experiment_manager.get_active_experiment()
            if active_exp:
                new_session.experiment_id = active_exp.experiment_id
                # 実験の参加者数とセッション数を更新
                experiment_manager.update_session_count(active_exp.experiment_id)
        
        session_manager.update_session(new_session)
        
        return new_session, condition

