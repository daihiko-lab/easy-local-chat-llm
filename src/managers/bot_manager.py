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
        self.default_system_prompt = "あなたは親切で役立つAIアシスタントです。ユーザーの質問に丁寧に答えてください。"
    
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
                               client_id: str) -> str:
        """
        ユーザーメッセージに対する応答を生成
        
        Args:
            user_message: ユーザーのメッセージ
            session_id: セッションID
            client_id: クライアントID（ユーザー）
            
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
            response = await asyncio.to_thread(
                ollama.chat,
                model=self.get_model(session_id),
                messages=messages
            )
            
            bot_message = response['message']['content']
            
            # ボットの応答を履歴に追加
            self.add_to_history(session_id, "assistant", bot_message)
            
            return bot_message
            
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
            
            # ストリーミング応答を生成
            full_response = ""
            stream = await asyncio.to_thread(
                ollama.chat,
                model=self.get_model(session_id),
                messages=messages,
                stream=True
            )
            
            for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    content = chunk['message']['content']
                    full_response += content
                    yield content
            
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

