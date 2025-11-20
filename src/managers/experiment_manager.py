import json
import os
from typing import Optional, List
from pathlib import Path
from datetime import datetime
from ..models.experiment_group import ExperimentGroup


class ExperimentManager:
    """実験管理クラス"""
    
    def __init__(self, base_dir: str = "data/experiments"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.current_experiment: Optional[ExperimentGroup] = None
        self.current_data_dir: Optional[Path] = None
    
    def create_experiment(self, name: str, description: str = "", researcher: str = "", slug: str = None) -> ExperimentGroup:
        """新しい実験グループを作成し、実験名ベースのフォルダを生成"""
        # スラッグ（ディレクトリ名）を生成
        if not slug:
            # 実験名から自動生成（英数字とアンダースコアのみ）
            import re
            slug = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
            slug = re.sub(r'_+', '_', slug)  # 連続するアンダースコアを1つに
            slug = slug.strip('_')  # 前後のアンダースコアを削除
            
            # 空の場合はタイムスタンプを使用
            if not slug:
                slug = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 既に存在する場合は番号を追加
            base_slug = slug
            counter = 1
            while (self.base_dir / slug).exists():
                slug = f"{base_slug}_{counter}"
                counter += 1
        
        data_dir = self.base_dir / slug
        
        # 既に存在する場合はエラー
        if data_dir.exists():
            raise ValueError(f"Experiment directory already exists: {slug}")
        
        # ディレクトリ構造を作成
        self._ensure_subdirectories(data_dir)
        
        # 実験グループを作成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_id = f"exp_{timestamp}"
        experiment = ExperimentGroup(
            experiment_id=experiment_id,
            name=name,
            slug=slug,
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
        
        print(f"📂 Created experiment directory: {slug}")
        
        return experiment
    
    def start_experiment(self, experiment_id: str):
        """実験を開始状態にする（他のアクティブな実験は自動的に一時停止）"""
        # 他のアクティブな実験を一時停止
        active_experiments = [exp for exp in self.get_all_experiments() if exp.status == "active"]
        for active_exp in active_experiments:
            if active_exp.experiment_id != experiment_id:
                print(f"⏸️  Pausing experiment: {active_exp.name} ({active_exp.experiment_id})")
                active_exp.status = "paused"
                self._save_experiment(active_exp, Path(active_exp.data_directory))
        
        # 指定された実験をアクティブに
        experiment = self.get_experiment(experiment_id)
        if experiment:
            experiment.status = "active"
            experiment.started_at = datetime.now().isoformat()
            data_dir = Path(experiment.data_directory)
            self._save_experiment(experiment, data_dir)
            
            # 現在の実験として設定
            self.current_experiment = experiment
            self.current_data_dir = data_dir
            
            print(f"✅ Experiment activated: {experiment.name} ({experiment_id})")
            print(f"📂 Using data directory: {data_dir.name}")
    
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
        """実験を再開する（他のアクティブな実験は自動的に一時停止）"""
        # 他のアクティブな実験を一時停止
        active_experiments = [exp for exp in self.get_all_experiments() if exp.status == "active"]
        for active_exp in active_experiments:
            if active_exp.experiment_id != experiment_id:
                print(f"⏸️  Pausing experiment: {active_exp.name} ({active_exp.experiment_id})")
                active_exp.status = "paused"
                self._save_experiment(active_exp, Path(active_exp.data_directory))
        
        # 指定された実験を再開
        experiment = self.get_experiment(experiment_id)
        if experiment and experiment.status == "paused":
            experiment.status = "active"
            data_dir = Path(experiment.data_directory)
            self._save_experiment(experiment, data_dir)
            
            # 現在の実験として設定
            self.current_experiment = experiment
            self.current_data_dir = data_dir
            
            print(f"▶️  Experiment resumed: {experiment.name} ({experiment_id})")
            print(f"📂 Using data directory: {data_dir.name}")
    
    def delete_experiment(self, experiment_id: str) -> bool:
        """実験を削除する"""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return False
        
        # 実験ファイルを削除
        for exp_dir in self.base_dir.iterdir():
            if exp_dir.is_dir():
                exp_file = exp_dir / "experiment.json"
                if exp_file.exists():
                    # experiment_idを確認
                    try:
                        with open(exp_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if data.get('experiment_id') == experiment_id:
                                exp_file.unlink()
                                print(f"[Experiment] Deleted: {experiment.name} ({experiment_id})")
                                return True
                    except Exception:
                        pass
        return False
    
    def get_experiment(self, experiment_id: str) -> Optional[ExperimentGroup]:
        """実験グループを取得"""
        for exp_dir in self.base_dir.iterdir():
            if exp_dir.is_dir():
                exp_file = exp_dir / "experiment.json"
                if exp_file.exists():
                    try:
                        with open(exp_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if data.get('experiment_id') == experiment_id:
                                return ExperimentGroup.from_dict(data)
                    except Exception as e:
                        print(f"Error loading experiment {exp_file}: {e}")
        return None
    
    def get_all_experiments(self) -> List[ExperimentGroup]:
        """全ての実験グループを取得"""
        experiments = []
        for exp_dir in sorted(self.base_dir.iterdir(), reverse=True):
            if exp_dir.is_dir():
                exp_file = exp_dir / "experiment.json"
                if exp_file.exists():
                    try:
                        with open(exp_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            experiments.append(ExperimentGroup.from_dict(data))
                    except Exception as e:
                        print(f"Error loading experiment {exp_file}: {e}")
        return experiments
    
    def get_active_experiment(self) -> Optional[ExperimentGroup]:
        """アクティブな実験を取得（複数ある場合は最新のもの）"""
        if self.current_experiment and self.current_experiment.status == "active":
            return self.current_experiment
        
        # メモリになければファイルから探す
        experiments = self.get_all_experiments()
        active_experiments = [exp for exp in experiments if exp.status == "active"]
        
        if len(active_experiments) > 1:
            # 複数のアクティブな実験がある場合（通常は起こらないはず）
            print(f"⚠️  Warning: Multiple active experiments found ({len(active_experiments)}). Using the most recent one.")
            # 最新のものを使用
            active_experiments.sort(key=lambda x: x.created_at, reverse=True)
            active_exp = active_experiments[0]
            
            # 他を一時停止
            for exp in active_experiments[1:]:
                print(f"⏸️  Auto-pausing: {exp.name} ({exp.experiment_id})")
                exp.status = "paused"
                self._save_experiment(exp, Path(exp.data_directory))
        elif len(active_experiments) == 1:
            active_exp = active_experiments[0]
        else:
            return None
        
        self.current_experiment = active_exp
        self.current_data_dir = Path(active_exp.data_directory)
        print(f"📂 Active experiment: {active_exp.name} (directory: {self.current_data_dir.name})")
        return active_exp
    
    def reload_experiment(self, experiment_id: str) -> Optional[ExperimentGroup]:
        """実験をファイルから再読み込みして、メモリ上のキャッシュを更新"""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return None
        
        # current_experimentがこの実験の場合、更新する
        if self.current_experiment and self.current_experiment.experiment_id == experiment_id:
            self.current_experiment = experiment
            self.current_data_dir = Path(experiment.data_directory)
            print(f"🔄 Reloaded experiment: {experiment.name} ({experiment_id})")
        # アクティブな実験の場合も更新（current_experimentがNoneでも）
        elif experiment.status == "active":
            self.current_experiment = experiment
            self.current_data_dir = Path(experiment.data_directory)
            print(f"🔄 Reloaded active experiment: {experiment.name} ({experiment_id})")
        
        return experiment
    
    def get_current_data_dir(self, force_new: bool = False) -> Path:
        """現在のデータディレクトリを取得
        
        Args:
            force_new: Trueの場合、強制的に新しいディレクトリを作成
        """
        if self.current_data_dir and not force_new:
            # ベースディレクトリ以外（実験ディレクトリ）の場合のみサブディレクトリを確保
            if self.current_data_dir != self.base_dir:
                self._ensure_subdirectories(self.current_data_dir)
            return self.current_data_dir
        
        # アクティブな実験があればそのディレクトリ
        active_exp = self.get_active_experiment()
        if active_exp and not force_new:
            self.current_data_dir = Path(active_exp.data_directory)
            self._ensure_subdirectories(self.current_data_dir)
            print(f"📂 Using active experiment data directory: {self.current_data_dir.name}")
            return self.current_data_dir
        
        # 強制的に新規作成しない場合は、既存の最新フォルダを探す
        if not force_new:
            # すべての実験ディレクトリから最新のものを探す
            all_experiments = self.get_all_experiments()
            if all_experiments:
                # 最新の実験（作成日時順）のディレクトリを使用
                all_experiments.sort(key=lambda x: x.created_at, reverse=True)
                latest_exp = all_experiments[0]
                data_dir = Path(latest_exp.data_directory)
                if data_dir.exists():
                    self._ensure_subdirectories(data_dir)
                    print(f"📂 Reusing latest experiment directory: {data_dir.name}")
                    self.current_data_dir = data_dir
                    return data_dir
            
            # 実験がない場合は、有効な実験ディレクトリを探す（後方互換性のため）
            # システムディレクトリ（conditions、messages、sessionsなど）を除外
            system_dirs = {"conditions", "messages", "sessions", "experiments", "exports"}
            existing_dirs = sorted(
                [d for d in self.base_dir.iterdir() 
                 if d.is_dir() and d.name not in system_dirs and not d.name.startswith('.')],
                key=lambda d: d.stat().st_mtime,
                reverse=True
            )
            if existing_dirs:
                data_dir = existing_dirs[0]
                self._ensure_subdirectories(data_dir)
                print(f"📂 Reusing existing experiment directory: {data_dir.name}")
                self.current_data_dir = data_dir
                return data_dir
        
        # 実験がない場合は、ベースディレクトリを返す（"default"ディレクトリは作らない）
        # 実際のデータは実験作成後に保存される
        data_dir = self.base_dir
        print(f"⚠️  Warning: No experiment found. Using base directory.")
        
        self.current_data_dir = data_dir
        return data_dir
    
    def _ensure_subdirectories(self, data_dir: Path):
        """必要なサブディレクトリが存在することを確認し、なければ作成"""
        subdirs = ["sessions", "messages", "exports"]
        for subdir in subdirs:
            (data_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    def _save_experiment(self, experiment: ExperimentGroup, data_dir: Path):
        """実験グループを保存"""
        exp_file = data_dir / "experiment.json"
        exp_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(exp_file, 'w', encoding='utf-8') as f:
            json.dump(experiment.to_dict(), f, ensure_ascii=False, indent=2)
    
    def recalculate_experiment_statistics(self, experiment_id: str, session_manager):
        """実験の統計を実際のセッションデータから再計算
        
        Args:
            experiment_id: 実験ID
            session_manager: SessionManagerインスタンス
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return
        
        # この実験に属する全セッションを取得
        all_sessions = session_manager.get_all_sessions()
        experiment_sessions = [s for s in all_sessions if s.experiment_id == experiment_id]
        
        # セッション数を計算
        total_sessions = len(experiment_sessions)
        
        # ユニークな参加者数を計算（全セッションの参加者をセットで集計）
        unique_participants = set()
        for session in experiment_sessions:
            unique_participants.update(session.participants)
        total_participants = len(unique_participants)
        
        # 実験データを更新
        experiment.total_sessions = total_sessions
        experiment.total_participants = total_participants
        
        data_dir = Path(experiment.data_directory)
        self._save_experiment(experiment, data_dir)
        
        print(f"[ExperimentManager] 📊 Statistics updated for {experiment_id}:")
        print(f"   Total sessions: {total_sessions}")
        print(f"   Total participants: {total_participants}")
    
    def update_participant_count(self, experiment_id: str, count: int):
        """参加者数を更新（非推奨：recalculate_experiment_statisticsを使用してください）"""
        experiment = self.get_experiment(experiment_id)
        if experiment:
            experiment.total_participants = count
            data_dir = Path(experiment.data_directory)
            self._save_experiment(experiment, data_dir)
    
    def update_session_count(self, experiment_id: str, count: int):
        """セッション数を更新（非推奨：recalculate_experiment_statisticsを使用してください）"""
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
            アクティブセッション数（参加者が1人以上いるセッションのみカウント）
        """
        sessions = session_manager.get_all_sessions()
        active_count = sum(
            1 for s in sessions 
            if s.experiment_id == experiment_id 
            and s.status == 'active'
            and len(s.participants) > 0  # 参加者がいるセッションのみカウント
        )
        print(f"[ExperimentManager] Active sessions for {experiment_id}: {active_count} (with participants)")
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
            print(f"[ExperimentManager] 🔢 Concurrent sessions: {active_count}/{experiment.max_concurrent_sessions}")
            if active_count >= experiment.max_concurrent_sessions:
                print(f"[ExperimentManager] ❌ Session limit reached! Cannot create new session.")
                return False, f"Maximum concurrent sessions reached ({experiment.max_concurrent_sessions})"
            else:
                print(f"[ExperimentManager] ✅ Can create session (within limit)")
        else:
            print(f"[ExperimentManager] ♾️  No session limit set (unlimited)")
        
        return True, ""

