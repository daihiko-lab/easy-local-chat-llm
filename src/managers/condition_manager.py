import json
import random
from typing import Optional, List, Tuple
from pathlib import Path
from datetime import datetime
from ..models.condition import Condition


class ConditionManager:
    """実験条件管理クラス"""
    
    def __init__(self, data_dir: str = None, condition_file: str = None, experiment_manager=None):
        """
        初期化
        
        Args:
            data_dir: 条件を保存するディレクトリ（condition_fileが指定されていない場合）
            condition_file: 条件ファイルのフルパス（優先）
            experiment_manager: ExperimentManagerインスタンス（動的ディレクトリ参照用）
        """
        self.experiment_manager = experiment_manager
        
        if condition_file:
            # ファイルパスが直接指定された場合
            self.condition_file = Path(condition_file)
            self.data_dir = self.condition_file.parent
        else:
            # ディレクトリが指定された場合
            self.data_dir = Path(data_dir or "data/conditions")
            self.condition_file = self.data_dir / "conditions.json"
        
        # ディレクトリは実際に使用する時（ファイル保存時）に作成される
        # 実験システムではデフォルト条件を自動作成しない（実験ごとに条件を作成）
    
    def _get_current_condition_file(self) -> Path:
        """現在のアクティブな実験の条件ファイルパスを取得"""
        if self.experiment_manager:
            current_dir = self.experiment_manager.get_current_data_dir()
            return current_dir / "conditions.json"
        return self.condition_file
    
    def _ensure_condition_dir(self, condition_file: Path):
        """条件ファイルの親ディレクトリを作成（実験ディレクトリの場合のみ）"""
        if self.experiment_manager:
            current_dir = self.experiment_manager.get_current_data_dir()
            # ベースディレクトリ以外（実験ディレクトリ）の場合のみ作成
            if current_dir != self.experiment_manager.base_dir:
                condition_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            condition_file.parent.mkdir(parents=True, exist_ok=True)
    
    
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
        
        # 動的パスを取得してファイルに保存
        condition_file = self._get_current_condition_file()
        self._ensure_condition_dir(condition_file)
        with open(condition_file, 'w', encoding='utf-8') as f:
            json.dump([c.to_dict() for c in conditions], f, ensure_ascii=False, indent=2)
        print(f"[ConditionManager] Saved condition to: {condition_file}")
    
    def get_condition(self, condition_id: str) -> Optional[Condition]:
        """条件を取得"""
        conditions = self.get_all_conditions()
        for condition in conditions:
            if condition.condition_id == condition_id:
                return condition
        return None
    
    def get_all_conditions(self) -> List[Condition]:
        """全条件を取得"""
        condition_file = self._get_current_condition_file()
        if not condition_file.exists():
            return []
        
        with open(condition_file, 'r', encoding='utf-8') as f:
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
        
        # 動的パスを取得して保存
        condition_file = self._get_current_condition_file()
        self._ensure_condition_dir(condition_file)
        with open(condition_file, 'w', encoding='utf-8') as f:
            json.dump([c.to_dict() for c in conditions], f, ensure_ascii=False, indent=2)
    
    def delete_condition(self, condition_id: str) -> bool:
        """条件を削除"""
        if condition_id == "default":
            return False  # デフォルト条件は削除不可
        
        conditions = self.get_all_conditions()
        conditions = [c for c in conditions if c.condition_id != condition_id]
        
        # 動的パスを取得して保存
        condition_file = self._get_current_condition_file()
        self._ensure_condition_dir(condition_file)
        with open(condition_file, 'w', encoding='utf-8') as f:
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
            print("[ConditionManager] ⚠️  No experiment conditions found")
            return None
        
        print(f"[ConditionManager] 🎲 Selecting from {len(experiment_conditions)} condition(s):")
        for cond in experiment_conditions:
            print(f"   - {cond.name} (Group: {cond.experiment_group}, Weight: {cond.weight})")
        
        # 重み付きランダム選択（累積分布を使用）
        weights = [c.weight for c in experiment_conditions]
        total_weight = sum(weights)
        
        # 0から総重みまでのランダムな値を生成
        rand_value = random.uniform(0, total_weight)
        
        # 累積重みで選択
        cumulative_weight = 0
        selected = experiment_conditions[0]  # フォールバック
        for condition, weight in zip(experiment_conditions, weights):
            cumulative_weight += weight
            if rand_value <= cumulative_weight:
                selected = condition
                break
        
        print(f"[ConditionManager] ✅ Selected: {selected.name} (Group: {selected.experiment_group})")
        
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
        
        session_manager.update_session(new_session)
        
        # 実験の統計を再計算（セッションを保存した後）
        if experiment_manager and new_session.experiment_id:
            experiment_manager.recalculate_experiment_statistics(new_session.experiment_id, session_manager)
        
        # セッション情報の記録をログ出力
        print(f"[ConditionManager] 📝 Session metadata recorded:")
        print(f"   Session ID: {new_session.session_id}")
        print(f"   Condition ID: {new_session.condition_id}")
        print(f"   Experiment Group: {new_session.experiment_group}")
        print(f"   Experiment ID: {new_session.experiment_id}")
        
        return new_session, condition

