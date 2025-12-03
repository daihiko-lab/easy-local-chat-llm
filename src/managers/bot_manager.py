import asyncio
from typing import Optional, List, Dict
import ollama
from datetime import datetime


class BotManager:
    """ローカルLLMボット管理クラス"""
    
    def __init__(self, default_model: str = "gemma3:4b", bot_client_id: str = "bot"):
        """
        初期化
        
        Args:
            default_model: デフォルトで使用するOllamaモデル名（デフォルト: gemma3:4b）
            bot_client_id: ボットのクライアントID
        """
        self.default_model = default_model
        self.bot_client_id = bot_client_id
        self.conversation_history: Dict[str, List[Dict]] = {}  # セッションIDごとの会話履歴
        self.system_prompts: Dict[str, str] = {}  # セッションIDごとのシステムプロンプト
        self.models: Dict[str, str] = {}  # セッションIDごとのモデル
        self.temperatures: Dict[str, float] = {}  # セッションIDごとのtemperature
        self.top_ps: Dict[str, float] = {}  # セッションIDごとのtop_p
        self.top_ks: Dict[str, int] = {}  # セッションIDごとのtop_k
        self.repeat_penalties: Dict[str, float] = {}  # セッションIDごとのrepeat_penalty
        self.num_predicts: Dict[str, Optional[int]] = {}  # セッションIDごとのnum_predict
        self.num_threads: Dict[str, Optional[int]] = {}  # セッションIDごとのnum_thread
        self.num_ctxs: Dict[str, Optional[int]] = {}  # セッションIDごとのnum_ctx
        self.num_gpus: Dict[str, Optional[int]] = {}  # セッションIDごとのnum_gpu
        self.num_batches: Dict[str, Optional[int]] = {}  # セッションIDごとのnum_batch
        self.default_system_prompt = "あなたは親切で役立つAIアシスタントです。ユーザーの質問に丁寧に答えてください。"
        self.default_temperature = 0.7
        self.default_top_p = 0.9
        self.default_top_k = 40
        self.default_repeat_penalty = 1.1
        self.default_num_predict = None
        # M4最適化デフォルト値
        self.default_num_thread = 8  # M4の10コアを活用
        self.default_num_ctx = 8192  # 16GBメモリで余裕を持たせる
        self.default_num_gpu = -1  # 全GPUレイヤー使用（M4 Neural Engine）
        self.default_num_batch = 512  # 並列処理最適化
    
    def set_model(self, session_id: str, model: str):
        """セッションのモデルを設定"""
        self.models[session_id] = model
    
    def get_model(self, session_id: str) -> str:
        """セッションのモデルを取得"""
        return self.models.get(session_id, self.default_model)
    
    def set_system_prompt(self, session_id: str, prompt: str):
        """セッションのシステムプロンプトを設定"""
        self.system_prompts[session_id] = prompt
    
    def get_system_prompt(self, session_id: str) -> str:
        """セッションのシステムプロンプトを取得"""
        return self.system_prompts.get(session_id, self.default_system_prompt)
    
    def set_temperature(self, session_id: str, temperature: float):
        """セッションのtemperatureを設定"""
        self.temperatures[session_id] = temperature
    
    def get_temperature(self, session_id: str) -> float:
        """セッションのtemperatureを取得"""
        return self.temperatures.get(session_id, self.default_temperature)
    
    def set_top_p(self, session_id: str, top_p: float):
        """セッションのtop_pを設定"""
        self.top_ps[session_id] = top_p
    
    def get_top_p(self, session_id: str) -> float:
        """セッションのtop_pを取得"""
        return self.top_ps.get(session_id, self.default_top_p)
    
    def set_top_k(self, session_id: str, top_k: int):
        """セッションのtop_kを設定"""
        self.top_ks[session_id] = top_k
    
    def get_top_k(self, session_id: str) -> int:
        """セッションのtop_kを取得"""
        return self.top_ks.get(session_id, self.default_top_k)
    
    def set_repeat_penalty(self, session_id: str, repeat_penalty: float):
        """セッションのrepeat_penaltyを設定"""
        self.repeat_penalties[session_id] = repeat_penalty
    
    def get_repeat_penalty(self, session_id: str) -> float:
        """セッションのrepeat_penaltyを取得"""
        return self.repeat_penalties.get(session_id, self.default_repeat_penalty)
    
    def set_num_predict(self, session_id: str, num_predict: Optional[int]):
        """セッションのnum_predictを設定"""
        self.num_predicts[session_id] = num_predict
    
    def get_num_predict(self, session_id: str) -> Optional[int]:
        """セッションのnum_predictを取得"""
        return self.num_predicts.get(session_id, self.default_num_predict)
    
    def set_num_thread(self, session_id: str, num_thread: Optional[int]):
        """セッションのnum_threadを設定"""
        self.num_threads[session_id] = num_thread
    
    def get_num_thread(self, session_id: str) -> Optional[int]:
        """セッションのnum_threadを取得"""
        return self.num_threads.get(session_id, self.default_num_thread)
    
    def set_num_ctx(self, session_id: str, num_ctx: Optional[int]):
        """セッションのnum_ctxを設定"""
        self.num_ctxs[session_id] = num_ctx
    
    def get_num_ctx(self, session_id: str) -> Optional[int]:
        """セッションのnum_ctxを取得"""
        return self.num_ctxs.get(session_id, self.default_num_ctx)
    
    def set_num_gpu(self, session_id: str, num_gpu: Optional[int]):
        """セッションのnum_gpuを設定"""
        self.num_gpus[session_id] = num_gpu
    
    def get_num_gpu(self, session_id: str) -> Optional[int]:
        """セッションのnum_gpuを取得"""
        return self.num_gpus.get(session_id, self.default_num_gpu)
    
    def set_num_batch(self, session_id: str, num_batch: Optional[int]):
        """セッションのnum_batchを設定"""
        self.num_batches[session_id] = num_batch
    
    def get_num_batch(self, session_id: str) -> Optional[int]:
        """セッションのnum_batchを取得"""
        return self.num_batches.get(session_id, self.default_num_batch)
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """セッションの会話履歴を取得"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        return self.conversation_history[session_id]
    
    def add_to_history(self, session_id: str, role: str, content: str):
        """会話履歴に追加
        
        注意: この履歴はAIが参照する会話履歴です。
        教示文(instruction)やシステムメッセージ(system)は含めないでください。
        """
        history = self.get_conversation_history(session_id)
        history.append({
            "role": role,
            "content": content
        })
        
        # 履歴が長くなりすぎないように制限（最新100件まで保持）
        if len(history) > 100:
            self.conversation_history[session_id] = history[-100:]
    
    def clear_history(self, session_id: str):
        """会話履歴をクリア"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
    
    async def generate_response(self, user_message: str, session_id: str, 
                               client_id: str, timeout: float = 300.0) -> str:
        """
        ユーザーメッセージに対する応答を生成
        
        Args:
            user_message: ユーザーのメッセージ
            session_id: セッションID
            client_id: クライアントID（ユーザー）
            timeout: タイムアウト秒数（デフォルト: 300秒 = 5分）
            
        Returns:
            ボットの応答メッセージ
        """
        try:
            # ユーザーメッセージを履歴に追加
            self.add_to_history(session_id, "user", user_message)
            
            # 会話履歴を取得
            history = self.get_conversation_history(session_id)
            
            # メッセージリストを構築（システムプロンプト + 会話履歴）
            messages = [
                {
                    "role": "system",
                    "content": self.get_system_prompt(session_id)
                }
            ]
            messages.extend(history)
            
            # Ollamaを使って応答を生成
            options = {
                'temperature': self.get_temperature(session_id),
                'top_p': self.get_top_p(session_id),
                'top_k': self.get_top_k(session_id),
                'repeat_penalty': self.get_repeat_penalty(session_id)
            }
            
            # オプションパラメータを追加（Noneでない場合のみ）
            num_predict = self.get_num_predict(session_id)
            if num_predict is not None:
                options['num_predict'] = num_predict
            
            num_thread = self.get_num_thread(session_id)
            if num_thread is not None:
                options['num_thread'] = num_thread
            
            num_ctx = self.get_num_ctx(session_id)
            if num_ctx is not None:
                options['num_ctx'] = num_ctx
            
            num_gpu = self.get_num_gpu(session_id)
            if num_gpu is not None:
                options['num_gpu'] = num_gpu
            
            num_batch = self.get_num_batch(session_id)
            if num_batch is not None:
                options['num_batch'] = num_batch
            
            # モニタリング情報を出力
            model = self.get_model(session_id)
            system_prompt = self.get_system_prompt(session_id)
            system_prompt_preview = system_prompt[:80] + "..." if len(system_prompt) > 80 else system_prompt
            
            print("\n" + "=" * 70)
            print("🤖 OLLAMA MODEL INVOCATION")
            print("=" * 70)
            print(f"Session ID    : {session_id[:20]}...")
            print(f"Model         : {model}")
            print(f"System Prompt : {system_prompt_preview}")
            print(f"\nParameters:")
            print(f"  temperature      : {options.get('temperature', 'N/A')}")
            print(f"  top_p            : {options.get('top_p', 'N/A')}")
            print(f"  top_k            : {options.get('top_k', 'N/A')}")
            print(f"  repeat_penalty   : {options.get('repeat_penalty', 'N/A')}")
            print(f"  num_predict      : {options.get('num_predict', 'Default (unlimited)')}")
            print(f"  num_thread       : {options.get('num_thread', 'Default (8)')}")
            print(f"  num_ctx          : {options.get('num_ctx', 'Default (8192)')}")
            print(f"  num_gpu          : {options.get('num_gpu', 'Default (-1, all)')}")
            print(f"  num_batch        : {options.get('num_batch', 'Default (512)')}")
            print(f"\nConversation History: {len(messages) - 1} messages")
            print(f"Timeout: {timeout}s")
            print("=" * 70 + "\n")
            
            # タイムアウト付きで応答を生成
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        ollama.chat,
                        model=model,
                        messages=messages,
                        options=options
                    ),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                print(f"⚠️ Response generation timed out after {timeout}s")
                # タイムアウト時は履歴から最後のユーザーメッセージを削除（応答がないため）
                if history and history[-1].get("role") == "user":
                    history.pop()
                return None  # タイムアウト時はNoneを返す
            
            bot_message = response['message']['content']
            
            # 応答の統計情報を出力
            print(f"✅ Response generated: {len(bot_message)} chars\n")
            
            # ボットの応答を履歴に追加
            self.add_to_history(session_id, "assistant", bot_message)
            
            return bot_message
            
        except asyncio.CancelledError:
            # キャンセル時（接続切断など）
            print(f"⚠️ [BotManager] Response generation cancelled for session {session_id[:12]}...")
            # 履歴から最後のユーザーメッセージを削除
            history = self.get_conversation_history(session_id)
            if history and history[-1].get("role") == "user":
                history.pop()
            return None  # キャンセル時はNoneを返す
        except Exception as e:
            error_message = f"申し訳ございません。エラーが発生しました: {str(e)}"
            print(f"[BotManager] Error generating response: {e}")
            return error_message
    
    async def stream_response(self, user_message: str, session_id: str, 
                             client_id: str):
        """
        ストリーミング応答を生成（将来の拡張用）
        
        Args:
            user_message: ユーザーのメッセージ
            session_id: セッションID
            client_id: クライアントID（ユーザー）
            
        Yields:
            ボットの応答のチャンク
        """
        try:
            # ユーザーメッセージを履歴に追加
            self.add_to_history(session_id, "user", user_message)
            
            # 会話履歴を取得
            history = self.get_conversation_history(session_id)
            
            # メッセージリストを構築
            messages = [
                {
                    "role": "system",
                    "content": self.get_system_prompt(session_id)
                }
            ]
            messages.extend(history)
            
            # オプションを構築
            options = {
                'temperature': self.get_temperature(session_id),
                'top_p': self.get_top_p(session_id),
                'top_k': self.get_top_k(session_id),
                'repeat_penalty': self.get_repeat_penalty(session_id)
            }
            
            # オプションパラメータを追加（Noneでない場合のみ）
            num_predict = self.get_num_predict(session_id)
            if num_predict is not None:
                options['num_predict'] = num_predict
            
            num_thread = self.get_num_thread(session_id)
            if num_thread is not None:
                options['num_thread'] = num_thread
            
            num_ctx = self.get_num_ctx(session_id)
            if num_ctx is not None:
                options['num_ctx'] = num_ctx
            
            num_gpu = self.get_num_gpu(session_id)
            if num_gpu is not None:
                options['num_gpu'] = num_gpu
            
            num_batch = self.get_num_batch(session_id)
            if num_batch is not None:
                options['num_batch'] = num_batch
            
            # モニタリング情報を出力
            model = self.get_model(session_id)
            system_prompt = self.get_system_prompt(session_id)
            system_prompt_preview = system_prompt[:80] + "..." if len(system_prompt) > 80 else system_prompt
            
            print("\n" + "=" * 70)
            print("🤖 OLLAMA MODEL INVOCATION (STREAMING)")
            print("=" * 70)
            print(f"Session ID    : {session_id[:20]}...")
            print(f"Model         : {model}")
            print(f"System Prompt : {system_prompt_preview}")
            print(f"\nParameters:")
            print(f"  temperature      : {options.get('temperature', 'N/A')}")
            print(f"  top_p            : {options.get('top_p', 'N/A')}")
            print(f"  top_k            : {options.get('top_k', 'N/A')}")
            print(f"  repeat_penalty   : {options.get('repeat_penalty', 'N/A')}")
            print(f"  num_predict      : {options.get('num_predict', 'Default (unlimited)')}")
            print(f"  num_thread       : {options.get('num_thread', 'Default (8)')}")
            print(f"  num_ctx          : {options.get('num_ctx', 'Default (8192)')}")
            print(f"  num_gpu          : {options.get('num_gpu', 'Default (-1, all)')}")
            print(f"  num_batch        : {options.get('num_batch', 'Default (512)')}")
            print(f"\nConversation History: {len(messages) - 1} messages")
            print("=" * 70 + "\n")
            
            # ストリーミング応答を生成
            full_response = ""
            stream = await asyncio.to_thread(
                ollama.chat,
                model=model,
                messages=messages,
                options=options,
                stream=True
            )
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    full_response += content
                    yield content
            
            # 応答の統計情報を出力
            print(f"✅ Streaming response completed: {len(full_response)} chars\n")
            
            # 完全な応答を履歴に追加
            self.add_to_history(session_id, "assistant", full_response)
            
        except Exception as e:
            error_message = f"申し訳ございません。エラーが発生しました: {str(e)}"
            print(f"[BotManager] Error in streaming response: {e}")
            yield error_message
    
    def is_bot_message(self, client_id: str) -> bool:
        """クライアントIDがボットかどうかを判定"""
        return client_id == self.bot_client_id
    
    @staticmethod
    def get_available_models() -> list:
        """Ollamaから利用可能なモデルのリストを取得"""
        try:
            models = ollama.list()
            
            # ollama-python 0.4.x は ListResponse オブジェクトを返す
            if hasattr(models, 'models'):
                # 各モデルは Model オブジェクトで、.model 属性にモデル名がある
                model_list = [model.model for model in models.models]
                print(f"[BotManager] Successfully loaded {len(model_list)} models: {model_list}")
                return model_list
            elif isinstance(models, dict) and 'models' in models:
                # 旧バージョン対応: 辞書形式
                model_list = [model.get('name', model.get('model', '')) for model in models['models']]
                print(f"[BotManager] Successfully loaded {len(model_list)} models (dict format): {model_list}")
                return model_list
            else:
                print(f"[BotManager] WARNING: Unexpected response format from ollama.list()")
                print(f"[BotManager] Response type: {type(models)}")
                return []
        except Exception as e:
            print(f"[BotManager] Failed to get available models: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def check_model_availability(self, model: str) -> bool:
        """
        指定されたOllamaモデルが利用可能かチェック
        
        Args:
            model: チェックするモデル名
            
        Returns:
            モデルが利用可能な場合True
        """
        try:
            # モデルリストを取得
            models = await asyncio.to_thread(ollama.list)
            available_models = [model_info['name'] for model_info in models.get('models', [])]
            
            # 指定されたモデルが利用可能かチェック
            is_available = any(model in model_name for model_name in available_models)
            
            if not is_available:
                print(f"[BotManager] Warning: Model '{model}' not found in available models.")
                print(f"[BotManager] Available models: {available_models}")
                print(f"[BotManager] Attempting to pull model...")
                
                # モデルをプル
                await asyncio.to_thread(ollama.pull, model)
                print(f"[BotManager] Successfully pulled model '{model}'")
                return True
            
            return True
            
        except Exception as e:
            print(f"[BotManager] Error checking model availability: {e}")
            return False

