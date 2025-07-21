import requests
import json
import time
from typing import Dict, Any, Optional
import asyncio

class DeepSeekClient:
    """DeepSeek AI 客户端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def chat_completion(
        self, 
        messages: list, 
        model: str = "deepseek-chat",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        调用DeepSeek聊天完成接口
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "..."}]
            model: 模型名称，默认为deepseek-chat
            temperature: 温度参数，控制随机性
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            API响应结果
        """
        try:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API调用失败: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"网络请求失败: {e}")
        except Exception as e:
            raise Exception(f"DeepSeek调用失败: {e}")
    
    def extract_content(self, response: Dict[str, Any]) -> str:
        """
        从API响应中提取内容
        
        Args:
            response: API响应结果
            
        Returns:
            提取的内容文本
        """
        try:
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
            
            raise Exception("无法从响应中提取内容")
            
        except Exception as e:
            raise Exception(f"内容提取失败: {e}")
    
    def simple_chat(self, prompt: str, system_prompt: str = None, model: str = "deepseek-chat") -> str:
        """
        简单的聊天接口
        
        Args:
            prompt: 用户输入
            system_prompt: 系统提示词
            model: 模型名称
            
        Returns:
            模型回复
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.chat_completion(messages, model=model)
            return self.extract_content(response)
        except Exception as e:
            print(f"DeepSeek API 调用出错: {e}")
            raise

    async def acreate_chat_completion(self, prompt: str, system_prompt: str = None, model: str = "deepseek-chat") -> str:
        """
        异步调用DeepSeek模型的简单聊天接口
        """
        try:
            def sync_call():
                return self.chat_completion(
                    [
                        {"role": "system", "content": system_prompt or "你是一个乐于助人的助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    model=model
                )

            response = await asyncio.to_thread(sync_call)
            if hasattr(response, "choices"):
                return response.choices[0].message.content
            elif isinstance(response, dict) and "choices" in response:
                return response["choices"][0]["message"]["content"]
            else:
                raise Exception("DeepSeek API 返回格式异常")
        except Exception as e:
            print(f"DeepSeek API 异步调用出错: {e}")
            raise

    def get_available_models(self) -> list:
        """获取可用的模型列表"""
        return [
            {
                "id": "deepseek-chat",
                "name": "DeepSeek-V3",
                "description": "DeepSeek最新的通用对话模型"
            },
            {
                "id": "deepseek-reasoner", 
                "name": "DeepSeek-R1",
                "description": "DeepSeek推理增强模型，具备强大的逻辑推理能力"
            }
        ] 