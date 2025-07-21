import requests
import base64
import json
import zlib
import re
import os
from typing import Dict, Any, Optional
from config_loader import config_loader
from oss_utils import oss_manager

class JDMapGenerator:
    def __init__(self):
        self.kroki_url = "https://kroki.io"
    
    def generate_jd_map(self, jd_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成JD岗位导图，返回Kroki可访问URL
        """
        try:
            mermaid_code = self._generate_mermaid_code_with_retry(jd_analysis)
            # 生成Kroki URL
            diagram_url = self._generate_kroki_url(mermaid_code)
            return {
                "mermaid_code": mermaid_code,
                "diagram_url": diagram_url,
                "success": True
            }
        except Exception as e:
            return {
                "mermaid_code": "",
                "diagram_url": None,
                "success": False,
                "error": str(e)
            }
    
    def _validate_mermaid_syntax(self, mermaid_code: str) -> bool:
        """使用Kroki API验证Mermaid语法是否正确"""
        if not mermaid_code.strip():
            return False
        try:
            response = requests.post(
                f"{self.kroki_url}/mermaid/svg",
                data=mermaid_code.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                timeout=15
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Kroki验证请求失败: {e}")
            return False

    def _generate_mermaid_code_with_retry(self, jd_analysis: Dict[str, Any]) -> str:
        """直接用模板生成Mermaid流程图源码，不再调用大模型和复杂prompt"""
        return self._generate_template_mermaid(jd_analysis)

    def _generate_mermaid_code(self, jd_analysis: Dict[str, Any]) -> str:
        """直接用模板生成Mermaid流程图源码，不再调用大模型和复杂prompt"""
        return self._generate_template_mermaid(jd_analysis)
    
    def _generate_template_mermaid(self, jd_analysis: Dict[str, Any]) -> str:
        """生成模板Mermaid代码"""
        job_title = jd_analysis.get("job_title", "软件工程师")
        skills = jd_analysis.get("skills", ["编程", "算法", "设计"])
        products = jd_analysis.get("products", ["通用技术"])
        
        mermaid_code = f'''
flowchart LR
    A[{job_title}] --> B[核心技能]
    A --> C[技术栈]
    A --> D[发展方向]
'''
        
        # 添加技能节点
        for i, skill in enumerate(skills[:3]):  # 最多显示3个技能
            mermaid_code += f'    B --> B{i+1}[{skill}]\n'
        
        # 添加产品节点
        for i, product in enumerate(products[:3]):  # 最多显示3个产品
            mermaid_code += f'    C --> C{i+1}[{product}]\n'
        
        # 添加发展方向
        mermaid_code += '''
    D --> D1[高级工程师]
    D --> D2[技术专家]
    D --> D3[架构师]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
'''
        
        return mermaid_code
    
    def _render_mermaid_to_png(self, mermaid_code: str) -> Optional[bytes]:
        """渲染Mermaid为PNG，并打印详细日志"""
        try:
            print("[Kroki调试] 发送Mermaid代码:\n", mermaid_code)
            response = requests.post(
                f"{self.kroki_url}/mermaid/svg",
                data=mermaid_code.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                timeout=20
            )
            print(f"[Kroki调试] 响应状态码: {response.status_code}")
            print(f"[Kroki调试] 响应内容: {response.text[:500]}")
            if response.status_code == 200:
                return response.content
            else:
                # 返回详细错误信息
                raise Exception(f"Kroki渲染失败: 状态码={response.status_code}, 内容={response.text}")
        except Exception as e:
            print(f"[Kroki调试] 渲染异常: {e}")
            raise
    
    def save_png_to_oss(self, png_data: bytes, filename: str) -> str:
        """保存PNG到OSS并返回URL"""
        try:
            # 生成OSS路径
            object_name = f"diagrams/{filename}.png"
            
            # 上传到OSS
            url = oss_manager.upload_bytes(png_data, object_name)
            
            return url
            
        except Exception as e:
            raise Exception(f"保存PNG到OSS失败: {e}")

    async def generate_jd_map_async(self, jd_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        异步生成JD岗位导图，返回Kroki可访问URL
        """
        try:
            mermaid_code = await self._generate_mermaid_code_with_retry_async(jd_analysis)
            diagram_url = self._generate_kroki_url(mermaid_code)
            return {
                "mermaid_code": mermaid_code,
                "diagram_url": diagram_url,
                "success": True
            }
        except Exception as e:
            return {
                "mermaid_code": "",
                "diagram_url": None,
                "success": False,
                "error": str(e)
            }

    async def _generate_mermaid_code_with_retry_async(self, jd_analysis: Dict[str, Any]) -> str:
        """异步流程也直接用模板生成Mermaid流程图源码"""
        return self._generate_template_mermaid(jd_analysis)

    async def _validate_mermaid_syntax_async(self, mermaid_code: str) -> bool:
        # 异步版本的语法验证
        # (需要使用像httpx这样的异步HTTP客户端)
        return True # Placeholder

    async def _render_mermaid_to_png_async(self, mermaid_code: str) -> Optional[bytes]:
        """异步版本的渲染 - 使用asyncio.to_thread包装同步方法"""
        import asyncio
        try:
            # 使用asyncio.to_thread将同步的HTTP请求包装为异步
            return await asyncio.to_thread(self._render_mermaid_to_png, mermaid_code)
        except Exception as e:
            print(f"[Kroki调试] 异步渲染异常: {e}")
            return None

    def _generate_kroki_url(self, mermaid_code: str) -> str:
        """
        生成Kroki渲染URL（SVG格式）
        """
        import zlib
        import base64
        # Kroki官方推荐：先zlib压缩，再base64-url-safe编码
        compressed = zlib.compress(mermaid_code.encode('utf-8'))
        b64 = base64.urlsafe_b64encode(compressed).decode('utf-8')
        # 去除末尾的'='填充
        b64 = b64.rstrip('=')
        return f"https://kroki.io/mermaid/svg/{b64}"

# 全局实例
jd_map_generator = JDMapGenerator() 