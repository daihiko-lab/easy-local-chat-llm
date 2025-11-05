import json
import os
from typing import Optional, List
from pathlib import Path
from datetime import datetime
from ..models.experiment_group import ExperimentGroup


class ExperimentManager:
    """実験管理クラス"""
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.current_experiment: Optional[ExperimentGroup] = None
        self.current_data_dir: Optional[Path] = None
    
    def create_experiment(self, name: str, description: str = "", researcher: str = "") -> ExperimentGroup:
        """新しい実験グループを作成し、タイムスタンプフォルダを生成"""
        # タイムスタンプフォルダ名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_dir = self.base_dir / timestamp
        
        # ディレクトリ構造を作成
        (data_dir / "experiments").mkdir(parents=True, exist_ok=True)
        (data_dir / "sessions").mkdir(parents=True, exist_ok=True)
        (data_dir / "messages").mkdir(parents=True, exist_ok=True)
        (data_dir / "exports").mkdir(parents=True, exist_ok=True)
        (data_dir / "templates").mkdir(parents=True, exist_ok=True)
        
        # 実験グループを作成
        experiment_id = f"exp_{timestamp}"
        experiment = ExperimentGroup(
            experiment_id=experiment_id,
            name=name,
            description=description,
            researcher=researcher,
            data_directory=str(data_dir),
            status="planning"
        )
        
        # 保存
        self._save_experiment(experiment, data_dir)
        
        # 現在の実験として設定
        self.current_experiment = experiment
        self.current_data_dir = data_dir
        
        return experiment
    
    def start_experiment(self, experiment_id: str):
        """実験を開始状態にする"""
        experiment = self.get_experiment(experiment_id)
        if experiment:
            experiment.status = "active"
            experiment.started_at = datetime.now().isoformat()
            data_dir = Path(experiment.data_directory)
            self._save_experiment(experiment, data_dir)
            
            # 現在の実験として設定
            self.current_experiment = experiment
            self.current_data_dir = data_dir
    
    def end_experiment(self, experiment_id: str):
        """実験を終了状態にする"""
        experiment = self.get_experiment(experiment_id)
        if experiment:
            experiment.status = "completed"
            experiment.ended_at = datetime.now().isoformat()
            data_dir = Path(experiment.data_directory)
            self._save_experiment(experiment, data_dir)
    
    def pause_experiment(self, experiment_id: str):
        """実験を一時中断状態にする"""
        experiment = self.get_experiment(experiment_id)
        if experiment and experiment.status == "active":
            experiment.status = "paused"
            data_dir = Path(experiment.data_directory)
            self._save_experiment(experiment, data_dir)
    
    def resume_experiment(self, experiment_id: str):
        """実験を再開する"""
        experiment = self.get_experiment(experiment_id)
        if experiment and experiment.status == "paused":
            experiment.status = "active"
            data_dir = Path(experiment.data_directory)
            self._save_experiment(experiment, data_dir)
    
    def delete_experiment(self, experiment_id: str) -> bool:
        """実験を削除する"""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return False
        
        # 実験ファイルを削除
        for exp_dir in self.base_dir.iterdir():
            if exp_dir.is_dir():
                exp_file = exp_dir / "experiments" / f"{experiment_id}.json"
                if exp_file.exists():
                    exp_file.unlink()
                    print(f"[Experiment] Deleted: {experiment.name} ({experiment_id})")
                    return True
        return False
    
    def get_experiment(self, experiment_id: str) -> Optional[ExperimentGroup]:
        """実験グループを取得"""
        for exp_dir in self.base_dir.iterdir():
            if exp_dir.is_dir():
                exp_file = exp_dir / "experiments" / f"{experiment_id}.json"
                if exp_file.exists():
                    with open(exp_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return ExperimentGroup.from_dict(data)
        return None
    
    def get_all_experiments(self) -> List[ExperimentGroup]:
        """全ての実験グループを取得"""
        experiments = []
        for exp_dir in sorted(self.base_dir.iterdir(), reverse=True):
            if exp_dir.is_dir():
                exp_groups_dir = exp_dir / "experiments"
                if exp_groups_dir.exists():
                    for exp_file in exp_groups_dir.glob("*.json"):
                        try:
                            with open(exp_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                experiments.append(ExperimentGroup.from_dict(data))
                        except Exception as e:
                            print(f"Error loading experiment {exp_file}: {e}")
        return experiments
    
    def get_active_experiment(self) -> Optional[ExperimentGroup]:
        """アクティブな実験を取得"""
        if self.current_experiment and self.current_experiment.status == "active":
            return self.current_experiment
        
        # メモリになければファイルから探す
        experiments = self.get_all_experiments()
        for exp in experiments:
            if exp.status == "active":
                self.current_experiment = exp
                self.current_data_dir = Path(exp.data_directory)
                return exp
        
        return None
    
    def get_current_data_dir(self, force_new: bool = False) -> Path:
        """現在のデータディレクトリを取得
        
        Args:
            force_new: Trueの場合、強制的に新しいディレクトリを作成
        """
        if self.current_data_dir and not force_new:
            return self.current_data_dir
        
        # アクティブな実験があればそのディレクトリ
        active_exp = self.get_active_experiment()
        if active_exp and not force_new:
            self.current_data_dir = Path(active_exp.data_directory)
            return self.current_data_dir
        
        # 強制的に新規作成しない場合は、既存の最新フォルダを探す
        if not force_new:
            existing_dirs = sorted(
                [d for d in self.base_dir.iterdir() 
                 if d.is_dir() and d.name.replace('_', '').isdigit() and len(d.name) == 15],
                reverse=True
            )
            if existing_dirs:
                data_dir = existing_dirs[0]
                print(f"📂 Using existing data directory: {data_dir.name}")
                self.current_data_dir = data_dir
                return data_dir
        
        # 新しいタイムスタンプフォルダを作成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        data_dir = self.base_dir / timestamp
        
        print(f"📂 Creating new data directory: {data_dir.name}")
        
        # 必要なサブディレクトリを作成
        (data_dir / "sessions").mkdir(parents=True, exist_ok=True)
        (data_dir / "messages").mkdir(parents=True, exist_ok=True)
        (data_dir / "conditions").mkdir(parents=True, exist_ok=True)
        (data_dir / "experiments").mkdir(parents=True, exist_ok=True)
        
        self.current_data_dir = data_dir
        return data_dir
    
    def _save_experiment(self, experiment: ExperimentGroup, data_dir: Path):
        """実験グループを保存"""
        exp_file = data_dir / "experiments" / f"{experiment.experiment_id}.json"
        exp_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(exp_file, 'w', encoding='utf-8') as f:
            json.dump(experiment.to_dict(), f, ensure_ascii=False, indent=2)
    
    def update_participant_count(self, experiment_id: str, count: int):
        """参加者数を更新"""
        experiment = self.get_experiment(experiment_id)
        if experiment:
            experiment.total_participants = count
            data_dir = Path(experiment.data_directory)
            self._save_experiment(experiment, data_dir)
    
    def update_session_count(self, experiment_id: str, count: int):
        """セッション数を更新"""
        experiment = self.get_experiment(experiment_id)
        if experiment:
            experiment.total_sessions = count
            data_dir = Path(experiment.data_directory)
            self._save_experiment(experiment, data_dir)
    
    def get_active_session_count(self, experiment_id: str, session_manager) -> int:
        """実験の現在のアクティブセッション数を取得
        
        Args:
            experiment_id: 実験ID
            session_manager: SessionManagerインスタンス
            
        Returns:
            アクティブセッション数
        """
        sessions = session_manager.get_all_sessions()
        active_count = sum(
            1 for s in sessions 
            if s.experiment_id == experiment_id and s.status == 'active'
        )
        print(f"[ExperimentManager] Active sessions for {experiment_id}: {active_count}")
        return active_count
    
    def can_create_session(self, experiment_id: str, session_manager) -> tuple[bool, str]:
        """セッションを作成できるかチェック
        
        Args:
            experiment_id: 実験ID
            session_manager: SessionManagerインスタンス
            
        Returns:
            (作成可能か, エラーメッセージまたは空文字)
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return False, "Experiment not found"
        
        if experiment.status != 'active':
            return False, f"Experiment is not active (status: {experiment.status})"
        
        # 同時セッション数制限のチェック
        if experiment.max_concurrent_sessions is not None:
            active_count = self.get_active_session_count(experiment_id, session_manager)
            print(f"[ExperimentManager] Checking limit: {active_count}/{experiment.max_concurrent_sessions}")
            if active_count >= experiment.max_concurrent_sessions:
                print(f"[ExperimentManager] ❌ Limit reached!")
                return False, f"Maximum concurrent sessions reached ({experiment.max_concurrent_sessions})"
        else:
            print(f"[ExperimentManager] No session limit set (unlimited)")
        
        return True, ""

