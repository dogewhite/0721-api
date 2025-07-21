from typing import Dict, Any, Optional, List
from enum import Enum
import asyncio
from deepseek_client import DeepSeekClient
from config_loader import config_loader

class ModelProvider(Enum):
    DEEPSEEK = "deepseek"

class LLMManager:
    """统一的LLM模型管理器"""
    
    def __init__(self):
        # 初始化DeepSeek客户端
        try:
            deepseek_key = config_loader.get_deepseek_api_key()
            if deepseek_key:
                self.deepseek_client = DeepSeekClient(deepseek_key)
        except Exception as e:
            print(f"DeepSeek 客户端初始化失败: {e}")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取所有可用的模型列表"""
        models = []
        
        # DeepSeek 模型
        if self.deepseek_client:
            models.extend([
                {
                    "id": "deepseek-chat",
                    "name": "DeepSeek-V1",
                    "provider": "deepseek",
                    "description": "DeepSeek最新的通用对话模型",
                    "available": True
                },
                {
                    "id": "deepseek-reasoner",
                    "name": "DeepSeek-R3",
                    "provider": "deepseek", 
                    "description": "DeepSeek推理增强模型，具备强大的逻辑推理能力",
                    "available": True
                }
            ])
        
        return models
    
    def chat(self, messages: List[Dict[str, str]], model_id: str = "deepseek-chat", **kwargs) -> str:
        """
        统一的聊天接口
        
        Args:
            messages: 消息列表
            model_id: 模型ID
            **kwargs: 其他参数
            
        Returns:
            模型回复
        """
        try:
            if not self.deepseek_client:
                raise Exception("DeepSeek 客户端未初始化")
            response = self.deepseek_client.chat_completion(messages, model=model_id, **kwargs)
            return self.deepseek_client.extract_content(response)
                
        except Exception as e:
            print(f"LLM调用出错 (模型: {model_id}): {e}")
            raise
    
    def simple_chat(self, prompt: str, system_prompt: str = None, model_id: str = "deepseek-chat") -> str:
        """
        简单的聊天接口
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            model_id: 模型ID
            
        Returns:
            模型回复
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        return self.chat(messages, model_id)
    
    async def achat(self, messages: List[Dict[str, str]], model_id: str = "deepseek-chat", **kwargs) -> str:
        """
        异步聊天接口
        
        Args:
            messages: 消息列表
            model_id: 模型ID
            **kwargs: 其他参数
            
        Returns:
            模型回复
        """
        try:
            if not self.deepseek_client:
                raise Exception("DeepSeek 客户端未初始化")
            
            def sync_call():
                response = self.deepseek_client.chat_completion(messages, model=model_id, **kwargs)
                return self.deepseek_client.extract_content(response)
            
            return await asyncio.to_thread(sync_call)
                
        except Exception as e:
            print(f"异步LLM调用出错 (模型: {model_id}): {e}")
            raise
    
    async def asimple_chat(self, prompt: str, system_prompt: str = None, model_id: str = "deepseek-chat") -> str:
        """
        异步简单聊天接口
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            model_id: 模型ID
            
        Returns:
            模型回复
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        return await self.achat(messages, model_id)

# 全局LLM管理器实例
llm_manager = LLMManager() 