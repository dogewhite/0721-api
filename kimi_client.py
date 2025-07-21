import requests
import json
import time
from typing import Dict, Any, Optional, List



class KimiClient:
    def __init__(self):
        self.api_key = self._load_api_key()
        self.base_url = "https://api.moonshot.cn/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _load_api_key(self) -> str:
        try:
            with open("kimi_config.txt", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        return line
        except Exception as e:
            print(f"读取KIMI API Key失败: {e}")
        return ""

    def upload_file(self, file_content: bytes, filename: str) -> Optional[str]:
        url = f"{self.base_url}/files"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {
            'file': (filename, file_content, 'application/octet-stream'),
            'purpose': (None, 'file-extract')
        }
        try:
            resp = requests.post(url, headers=headers, files=files, timeout=30)
            if resp.status_code == 200:
                return resp.json().get('id')
            else:
                print(f"Kimi文件上传失败: {resp.status_code}, {resp.text}")
        except Exception as e:
            print(f"Kimi文件上传异常: {e}")
        return None

    def check_file_status(self, file_id: str) -> bool:
        """检查文件是否已处理完成"""
        url = f"{self.base_url}/files/{file_id}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            print(f"检查文件状态响应: {resp.status_code}")
            if resp.status_code == 200:
                file_info = resp.json()
                print(f"文件信息: {json.dumps(file_info, indent=2, ensure_ascii=False)}")
                
                # 检查文件状态，Kimi API 可能使用不同的状态值
                status = file_info.get('status', '')
                print(f"文件状态: {status}")
                
                # 扩展状态检查，包含更多可能的状态值
                completed_statuses = ['processed', 'completed', 'ready', 'finished', 'success', 'ok']
                return status in completed_statuses
            else:
                print(f"检查文件状态失败: {resp.status_code}, {resp.text}")
        except Exception as e:
            print(f"检查文件状态异常: {e}")
        return False

    def standardize_resume_by_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        # 读取文件内容
        file_content = self._read_file_content(file_id)
        if not file_content:
            print(f"无法读取文件内容，文件ID: {file_id}")
            return None
            
        url = f"{self.base_url}/chat/completions"
        prompt = self._build_standardization_prompt()
        
        # 一次性提取所有信息并生成AI分析
        complete_instruction = """请从简历中提取所有信息并生成AI分析，输出完整的JSON格式：

{
  "basic_info": {
    "name": "姓名",
    "gender": "性别",
    "birth_date": "出生日期",
    "age": "年龄"
  },
  "contact_info": {
    "phone": "电话",
    "email": "邮箱",
    "address": "地址"
  },
  "summary": {
    "work_years": "工作年限",
    "skills": "技能",
    "languages": "语言能力"
  },
  "expectations": {
    "expected_position": "期望职位",
    "expected_salary": "期望薪资",
    "expected_location": "期望地点"
  },
  "work_experiences": [
    {
      "company_name": "公司名称",
      "position": "职位",
      "start_date": "开始日期",
      "end_date": "结束日期",
      "current_status": "在职/离职",
      "job_description": "工作描述"
    }
  ],
  "education_experiences": [
    {
      "school_name": "学校名称",
      "major": "专业",
      "degree": "学位",
      "start_date": "开始日期",
      "end_date": "结束日期"
    }
  ],
  "project_experiences": [
    {
      "project_name": "项目名称",
      "role": "角色",
      "start_date": "开始日期",
      "end_date": "结束日期",
      "project_description": "项目描述"
    }
  ],
  "ai_analysis": {
    "ai_profile": "AI生成的个人简介",
    "ai_swot": "AI生成的SWOT分析",
    "ai_career_stage": "AI判断的职业阶段",
    "ai_personality": "AI分析的性格特点"
  }
}

注意：
1. 提取所有可用的信息
2. 确保JSON格式正确
3. 如果信息不存在，设为null
4. 工作经历、教育经历、项目经历都是数组格式
5. 基于提取的信息生成AI分析，包括个人简介、SWOT分析、职业阶段判断和性格特点分析"""
        
        # 构建messages
        messages = [
            {"role": "system", "content": prompt},
            {"role": "system", "content": file_content},
            {"role": "user", "content": complete_instruction}
        ]
        
        payload = {
            "model": "moonshot-v1-128k",
            "messages": messages,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "max_tokens": 40000,
            "top_p": 0.95
        }
        
        print("=== 开始一次性提取所有简历信息并生成AI分析 ===")
        
        # 添加重试机制
        max_retries = 3
        for retry in range(max_retries):
            try:
                print(f"正在发送完整简历处理请求到Kimi API... (尝试 {retry + 1}/{max_retries})")
                resp = requests.post(url, headers=self.headers, json=payload, timeout=180)
                print(f"Kimi API响应状态码: {resp.status_code}")
                
                if resp.status_code == 200:
                    response_data = resp.json()
                    content = response_data['choices'][0]['message']['content']
                    print(f"返回内容长度: {len(content)}")
                    
                    try:
                        result = json.loads(content)
                        print("JSON解析成功")
                        print(f"最终结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return result
                        
                    except json.JSONDecodeError as e:
                        print(f"JSON解析失败: {e}")
                        # 尝试修复JSON
                        try:
                            content_clean = content.strip().lstrip('\ufeff')
                            last_brace = content_clean.rfind('}')
                            if last_brace > 0:
                                content_clean = content_clean[:last_brace+1]
                                result = json.loads(content_clean)
                                print(f"修复后解析成功")
                                print(f"最终结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
                                return result
                        except Exception as fix_error:
                            print(f"修复JSON失败: {fix_error}")
                
                elif resp.status_code == 429:
                    # 遇到限流错误，等待更长时间
                    wait_time = (retry + 1) * 15  # 递增等待时间
                    print(f"遇到RPM限制，等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"请求失败: {resp.status_code}, {resp.text}")
                    if retry < max_retries - 1:
                        print(f"等待8秒后重试...")
                        time.sleep(8)
                    else:
                        print(f"所有重试都失败了")
                    
            except Exception as e:
                print(f"请求异常: {e}")
                if retry < max_retries - 1:
                    print(f"等待8秒后重试...")
                    time.sleep(8)
                else:
                    import traceback
                    traceback.print_exc()
        
        return None

    def _generate_ai_analysis(self, resume_data: dict, file_content: str) -> dict:
        """生成AI分析部分（已废弃，现在在一次性请求中完成）"""
        print("警告：此方法已废弃，AI分析现在在一次性请求中完成")
        return {
            "ai_profile": None,
            "ai_swot": None,
            "ai_career_stage": None,
            "ai_personality": None
        }

    def _read_file_content(self, file_id: str) -> Optional[str]:
        """读取文件内容"""
        url = f"{self.base_url}/files/{file_id}/content"
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            if resp.status_code == 200:
                return resp.text
            else:
                print(f"读取文件内容失败: {resp.status_code}, {resp.text}")
        except Exception as e:
            print(f"读取文件内容异常: {e}")
        return None



    def standardize_resume(self, file_id: str) -> Optional[Dict[str, Any]]:
        """标准化简历的别名方法，保持向后兼容"""
        return self.standardize_resume_by_file(file_id)

    def standardize_resume_with_progress(self, file_id: str) -> Optional[Dict[str, Any]]:
        """带进度反馈的简历标准化方法"""
        # 直接调用主方法，因为现在都是一次性处理
        print("=== 开始带进度反馈的简历处理 ===")
        print("进度: 0% - 准备中...")
        
        result = self.standardize_resume_by_file(file_id)
        
        if result:
            print("进度: 100% - 完成!")
            return result
        else:
            print("进度: 100% - 处理失败!")
            return None

    def _build_standardization_prompt(self) -> str:
        """读取简历标准化prompt"""
        try:
            with open("resume_standardization_prompt.txt", "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"读取简历标准化prompt失败: {e}")
            raise Exception(f"无法读取简历标准化prompt文件: {e}")

    def test_file_processing(self, file_id: str) -> bool:
        """测试文件处理流程的每个步骤"""
        print(f"\n=== 开始测试文件处理流程 ===")
        print(f"文件ID: {file_id}")
        
        # 步骤1: 检查文件状态
        print(f"\n步骤1: 检查文件状态")
        if self.check_file_status(file_id):
            print("✓ 文件状态检查通过")
        else:
            print("✗ 文件状态检查失败")
            return False
        
        # 步骤2: 读取文件内容
        print(f"\n步骤2: 读取文件内容")
        file_content = self._read_file_content(file_id)
        if file_content:
            print(f"✓ 文件内容读取成功，长度: {len(file_content)}")
            print(f"文件内容前200字符: {file_content[:200]}...")
        else:
            print("✗ 文件内容读取失败")
            return False
        
        # 步骤3: 构建prompt
        print(f"\n步骤3: 构建prompt")
        try:
            prompt = self._build_standardization_prompt()
            print(f"✓ Prompt构建成功，长度: {len(prompt)}")
        except Exception as e:
            print(f"✗ Prompt构建失败: {e}")
            return False
        
        # 步骤4: 测试API调用
        print(f"\n步骤4: 测试API调用")
        result = self.standardize_resume_by_file(file_id)
        if result:
            print("✓ API调用成功")
            return True
        else:
            print("✗ API调用失败")
            return False 
        
    def _fix_work_experience_json(self, content: str) -> str:
        """修复工作经历JSON格式"""
        try:
            # 1. 移除可能的BOM标记
            content = content.strip().lstrip('\ufeff')
            
            # 2. 查找JSON开始和结束位置
            start_brace = content.find('{')
            end_brace = content.rfind('}')
            
            if start_brace == -1 or end_brace == -1:
                raise ValueError("找不到有效的JSON结构")
            
            # 3. 提取JSON部分
            json_content = content[start_brace:end_brace+1]
            
            # 4. 修复常见的JSON问题
            # 修复未闭合的字符串
            json_content = self._fix_unclosed_strings(json_content)
            
            # 修复缺少的逗号
            json_content = self._fix_missing_commas(json_content)
            
            # 5. 验证JSON格式
            json.loads(json_content)  # 测试是否可以解析
            
            return json_content
            
        except Exception as e:
            print(f"JSON修复失败: {e}")
            # 如果修复失败，尝试最简单的修复
            last_brace = content.rfind('}')
            if last_brace > 0:
                return content[:last_brace+1]
            raise e

    def _fix_unclosed_strings(self, content: str) -> str:
        """修复未闭合的字符串"""
        # 统计引号数量，确保成对出现
        single_quotes = content.count("'")
        double_quotes = content.count('"')
        
        # 如果单引号是奇数，在末尾添加一个
        if single_quotes % 2 == 1:
            content += "'"
        
        # 如果双引号是奇数，在末尾添加一个
        if double_quotes % 2 == 1:
            content += '"'
        
        return content

    def _fix_missing_commas(self, content: str) -> str:
        """修复缺少的逗号"""
        # 在数组元素之间添加缺少的逗号
        import re
        
        # 修复数组元素之间缺少的逗号
        # 匹配 "value1" "value2" 模式，在中间添加逗号
        content = re.sub(r'"\s*"', '", "', content)
        
        # 修复对象属性之间缺少的逗号
        # 匹配 "key": value "key2": value2 模式
        content = re.sub(r'(\d+|[a-zA-Z_][a-zA-Z0-9_]*)\s*"([^"]+)":', r'\1, "\2":', content)
        
        return content

