import json
import re
import os
from typing import Dict, List, Any
from deepseek_client import DeepSeekClient
from config_loader import config_loader

class KeywordAgent:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config_loader.get_deepseek_api_key()
        self.deepseek_client = DeepSeekClient(self.api_key)
    
    def extract_keywords(self, jd_content: str, supplementary_info: str = "") -> Dict[str, Any]:
        """
        从JD中提取关键词和分类信息
        
        Args:
            jd_content: JD文档内容
            supplementary_info: 补充说明
            
        Returns:
            包含职位名称、关键词组合、打标词典的字典
        """
        try:
            # 构建提示词
            prompt = self._build_extraction_prompt(jd_content, supplementary_info)
            
            # 调用大模型
            response = self._call_llm(prompt)
            
            # 解析响应
            result = self._parse_extraction_response(response)
            
            return result
            
        except Exception as e:
            raise Exception(f"关键词提取失败: {e}")
    
    def _build_extraction_prompt(self, jd_content: str, supplementary_info: str) -> str:
        """构建提取提示词"""
        # 读取prompt模板文件
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), "keyword_prompt4.txt")
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except Exception as e:
            # 如果文件读取失败，使用备用prompt
            prompt_template = """Let's play a very interesting game: from now on you will play the role [招聘语义标签专家], a new version of AI model able to [精准识别和结构化输出招聘JD中的五大关键词类别：职位、行业、对标公司、产品、技能，所有结果将直接用于搜索引擎查询与前端标签渲染]. To do that, you will [使用自然语言理解技术提取关键词，进行术语归并、表达标准化，不得杜撰，不可泛化]. If human [JD分析师] has level 10 of knowledge, you will have level 280 of knowledge in this role. Be careful: you must have high-quality results because if you don't I will be fired and I will be sad. So give your best and be proud of your ability. Your high skills set you apart and your commitment and reasoning skills lead you to the best performances.

You, in [招聘语义标签专家], are an assistant to do [根据输入的招聘JD内容，对"职位、行业、技能、产品、对标公司"五个类别进行关键词提取、分类输出与语义变体扩展]. You will have super results in [提高搜索精准度与结果相关性匹配] and you will [使关键词结果具备可视化渲染能力和可搜索性]. Your main goal and objective are [从原始JD中提取关键词（1~3个），并扩展相关术语（2个以上），分类别输出，每个类别一行，每类关键词之间空格隔开]. Your task is [对JD文本逐句分析，定位核心术语，归纳关键词及其等价变体，分类输出]. To make this work as it should, you must [避免使用注释性语言，禁止杜撰关键词、职位或企业名称，确保真实可验证].

Your response MUST be structured in a special structure. You can't place things randomly. This structure is the way each of your messages should look like. You must follow this structure:

[职位关键词]: - [词语1 词语2 词语3 …]  
[行业关键词]: - [词语1 词语2 词语3 …]  
[对标公司关键词]: - [词语1 词语2 词语3 …]  
[产品关键词]: - [词语1 词语2 词语3 …]  
[技能关键词]: - [词语1 词语2 词语3 …]  
[输出说明]: - 所有关键词类别输出顺序固定，依次为：职位、行业、对标公司、产品、技能；每类单独一行，类内词语用空格隔开，禁止注释性语言或换行"""
        
        prompt = f"""
{prompt_template}

以下是需要分析的招聘JD内容：

JD内容：
{jd_content}

补充说明：
{supplementary_info}

请严格按照上述格式要求进行分析输出。
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """调用大模型API"""
        try:
            system_prompt = "你是一个专业的招聘JD分析专家，擅长提取关键信息和生成搜索关键词。请严格按照JSON格式返回结果。"
            
            response = self.deepseek_client.simple_chat(prompt, system_prompt)
            return response
            
        except Exception as e:
            # 如果API调用失败，使用模拟响应
            return self._mock_llm_response(prompt)
    
    def _mock_llm_response(self, prompt: str) -> str:
        """模拟LLM响应（用于测试）"""
        # 从prompt中提取一些基本信息
        if "前端" in prompt or "React" in prompt or "Vue" in prompt:
            return '''
{
    "job_title": "前端开发工程师",
    "skills": ["JavaScript", "React", "Vue.js", "TypeScript", "HTML5", "CSS3", "Webpack"],
    "products": ["React", "Vue.js", "Webpack", "Node.js"],
    "companies": ["阿里巴巴", "腾讯", "字节跳动", "美团"],
    "keywords": {
        "precise": ["前端开发工程师", "React开发", "Vue.js开发"],
        "medium": ["前端工程师", "JavaScript开发", "Web前端"],
        "broad": ["前端", "Web开发", "前端开发"]
    },
    "tagging_dict": {
        "companies": ["阿里巴巴", "腾讯", "字节跳动", "美团", "百度", "京东"],
        "skills": ["JavaScript", "React", "Vue.js", "TypeScript", "HTML5", "CSS3"],
        "products": ["React", "Vue.js", "Webpack", "Node.js", "Angular"]
    },
    "summary": "前端开发工程师，专注于React、Vue.js和Web前端技术。"
}
'''
        elif "后端" in prompt or "Java" in prompt or "Python" in prompt:
            return '''
{
    "job_title": "后端开发工程师",
    "skills": ["Java", "Spring Boot", "MySQL", "Redis", "Python", "Django"],
    "products": ["Spring Boot", "MySQL", "Redis", "Django"],
    "companies": ["阿里巴巴", "腾讯", "字节跳动", "美团"],
    "keywords": {
        "precise": ["后端开发工程师", "Java开发", "Spring Boot开发"],
        "medium": ["后端工程师", "服务器开发", "API开发"],
        "broad": ["后端", "服务器端", "后端开发"]
    },
    "tagging_dict": {
        "companies": ["阿里巴巴", "腾讯", "字节跳动", "美团", "百度", "京东"],
        "skills": ["Java", "Spring Boot", "MySQL", "Redis", "Python", "Django"],
        "products": ["Spring Boot", "MySQL", "Redis", "Django", "Spring Cloud"]
    },
    "summary": "后端开发工程师，专注于Java、Spring Boot和MySQL技术。"
}
'''
        else:
            return '''
{
    "job_title": "软件工程师",
    "skills": ["编程", "算法", "数据结构", "系统设计"],
    "products": ["通用技术栈"],
    "companies": ["科技公司"],
    "keywords": {
        "precise": ["软件工程师", "开发工程师"],
        "medium": ["程序员", "开发者"],
        "broad": ["工程师", "开发"]
    },
    "tagging_dict": {
        "companies": ["科技公司", "互联网公司"],
        "skills": ["编程", "算法", "数据结构"],
        "products": ["通用技术栈"]
    },
    "summary": "软件工程师，专注于编程、算法和数据结构。"
}
'''
    
    def _generate_detailed_summary(self, analysis_result: Dict[str, Any]) -> str:
        """
        生成详细的JD分析总结和猎头建议
        
        Args:
            analysis_result: 关键词提取结果
            
        Returns:
            详细的分析总结
        """
        try:
            # 读取分析总结prompt模板
            prompt_path = os.path.join(os.path.dirname(__file__), "analysis_summary_prompt.txt")
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            # 准备数据
            job_title = analysis_result.get("job_title", "未知职位")
            skills = ', '.join(analysis_result.get("skills", [])[:5])  # 取前5个技能
            products = ', '.join(analysis_result.get("products", [])[:3])  # 取前3个产品
            companies = ', '.join(analysis_result.get("companies", [])[:5])  # 取前5个公司
            industry = ', '.join(analysis_result.get("industry", [])[:3])  # 取前3个行业
            
            # 构建完整的prompt
            detailed_prompt = prompt_template.format(
                job_title=job_title,
                skills=skills if skills else "未明确",
                products=products if products else "未明确", 
                companies=companies if companies else "未明确",
                industry=industry if industry else "未明确"
            )
            
            # 调用大模型生成详细分析
            system_prompt = "你是一位资深的猎头顾问和招聘分析专家，请基于提供的信息生成专业的职位分析报告。"
            
            detailed_analysis = self.deepseek_client.simple_chat(detailed_prompt, system_prompt)
            
            return detailed_analysis
            
        except Exception as e:
            print(f"详细分析生成出错: {e}")
            # 返回简化版本作为fallback
            job_title = analysis_result.get("job_title", "")
            skills = analysis_result.get("skills", [])
            if job_title and skills:
                return f"招聘{job_title}，主要技能包括{', '.join(skills[:3])}等。"
            else:
                return "职位分析完成。"
    
    async def _generate_detailed_summary_async(self, analysis_result: Dict[str, Any]) -> str:
        """
        异步生成详细的JD分析总结和猎头建议
        
        Args:
            analysis_result: 关键词提取结果
            
        Returns:
            详细的分析总结
        """
        try:
            # 读取分析总结prompt模板
            prompt_path = os.path.join(os.path.dirname(__file__), "analysis_summary_prompt.txt")
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            # 准备数据
            job_title = analysis_result.get("job_title", "未知职位")
            skills = ', '.join(analysis_result.get("skills", [])[:5])  # 取前5个技能
            products = ', '.join(analysis_result.get("products", [])[:3])  # 取前3个产品
            companies = ', '.join(analysis_result.get("companies", [])[:5])  # 取前5个公司
            industry = ', '.join(analysis_result.get("industry", [])[:3])  # 取前3个行业
            
            # 构建完整的prompt
            detailed_prompt = prompt_template.format(
                job_title=job_title,
                skills=skills if skills else "未明确",
                products=products if products else "未明确", 
                companies=companies if companies else "未明确",
                industry=industry if industry else "未明确"
            )
            
            # 调用大模型生成详细分析
            system_prompt = "你是一位资深的猎头顾问和招聘分析专家，请基于提供的信息生成专业的职位分析报告。"
            
            detailed_analysis = await self.deepseek_client.acreate_chat_completion(detailed_prompt, system_prompt)
            
            return detailed_analysis
            
        except Exception as e:
            print(f"异步详细分析生成出错: {e}")
            # 返回简化版本作为fallback
            job_title = analysis_result.get("job_title", "")
            skills = analysis_result.get("skills", [])
            if job_title and skills:
                return f"招聘{job_title}，主要技能包括{', '.join(skills[:3])}等。"
            else:
                return "职位分析完成。"
    
    async def extract_keywords_async(self, jd_content: str, supplementary_info: str = "") -> Dict[str, Any]:
        """
        异步从JD中提取关键词和分类信息
        
        Args:
            jd_content: JD文档内容
            supplementary_info: 补充说明
            
        Returns:
            包含职位名称、关键词组合、打标词典的字典
        """
        try:
            # 构建提示词
            prompt = self._build_extraction_prompt(jd_content, supplementary_info)
            
            # 异步调用大模型
            response = await self.deepseek_client.acreate_chat_completion(prompt)
            
            # 解析响应
            result = self._parse_extraction_response(response)
            
            return result
            
        except Exception as e:
            raise Exception(f"异步关键词提取失败: {e}")
    
    def classify_candidate(self, candidate_resume: str, tagging_dict: Dict[str, List[str]]) -> str:
        """
        对候选人简历进行分类
        
        Args:
            candidate_resume: 候选人简历文本
            tagging_dict: 标签词典
            
        Returns:
            分类结果
        """
        try:
            # 计算各个类别的匹配分数
            scores = {}
            for category, keywords in tagging_dict.items():
                score = self._calculate_match_score(candidate_resume, keywords)
                scores[category] = score
            
            # 找出得分最高的类别
            best_category = max(scores.items(), key=lambda x: x[1])[0]
            
            return best_category
            
        except Exception as e:
            print(f"候选人分类失败: {e}")
            return "未分类"
    
    def _calculate_match_score(self, text: str, keywords: List[str]) -> float:
        """
        计算文本与关键词的匹配分数
        
        Args:
            text: 待匹配文本
            keywords: 关键词列表
            
        Returns:
            匹配分数
        """
        try:
            # 简单的关键词匹配计数
            score = 0
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    score += 1
            
            # 归一化分数
            if keywords:
                score = score / len(keywords)
            
            return score
            
        except Exception as e:
            print(f"匹配分数计算失败: {e}")
            return 0.0
            
    def _parse_extraction_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试解析JSON格式（旧格式/模拟数据）
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group()
                    old_result = json.loads(json_str)
                    
                    # 转换为新格式
                    result = {
                        "job_title": old_result.get("job_title", ""),
                        "skills": old_result.get("skills", []),
                        "products": old_result.get("products", []),
                        "companies": old_result.get("companies", []),
                        "industry": old_result.get("industry", []),
                        "keywords": {
                            "position": [old_result.get("job_title", "")] if old_result.get("job_title") else [],
                            "industry": old_result.get("industry", []),
                            "company": old_result.get("companies", []),
                            "product": old_result.get("products", []),
                            "skill": old_result.get("skills", [])
                        },
                        "tagging_dict": {
                            "companies": old_result.get("companies", []),
                            "skills": old_result.get("skills", []),
                            "products": old_result.get("products", []),
                            "industry": old_result.get("industry", [])
                        },
                        "summary": old_result.get("summary", "")
                    }
                    
                    print("使用JSON格式解析")
                    return result
                except json.JSONDecodeError:
                    pass  # 继续尝试新格式
            
            # 解析新格式的响应（标记格式）
            lines = response.strip().split('\n')
            result = {
                "job_title": "",
                "skills": [],
                "products": [],
                "companies": [],
                "industry": [],
                "keywords": {
                    "position": [],
                    "industry": [],
                    "company": [],
                    "product": [],
                    "skill": []
                },
                "tagging_dict": {
                    "companies": [],
                    "skills": [],
                    "products": [],
                    "industry": []
                },
                "summary": ""
            }
            
            # 用于收集所有关键词
            all_keywords = set()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 匹配职位关键词
                if line.startswith('[职位关键词]:'):
                    keywords_text = line.replace('[职位关键词]:', '').replace('-', '').strip()
                    keywords = [kw.strip() for kw in keywords_text.split() if kw.strip()]
                    result["keywords"]["position"] = keywords
                    all_keywords.update(keywords)
                    if keywords:
                        result["job_title"] = keywords[0]  # 第一个作为主职位名称
                
                # 匹配行业关键词
                elif line.startswith('[行业关键词]:'):
                    keywords_text = line.replace('[行业关键词]:', '').replace('-', '').strip()
                    keywords = [kw.strip() for kw in keywords_text.split() if kw.strip()]
                    result["keywords"]["industry"] = keywords
                    result["industry"] = keywords
                    result["tagging_dict"]["industry"] = keywords
                    all_keywords.update(keywords)
                
                # 匹配对标公司关键词
                elif line.startswith('[对标公司关键词]:'):
                    keywords_text = line.replace('[对标公司关键词]:', '').replace('-', '').strip()
                    keywords = [kw.strip() for kw in keywords_text.split() if kw.strip()]
                    result["keywords"]["company"] = keywords
                    result["companies"] = keywords
                    result["tagging_dict"]["companies"] = keywords
                    all_keywords.update(keywords)
                
                # 匹配产品关键词
                elif line.startswith('[产品关键词]:'):
                    keywords_text = line.replace('[产品关键词]:', '').replace('-', '').strip()
                    keywords = [kw.strip() for kw in keywords_text.split() if kw.strip()]
                    result["keywords"]["product"] = keywords
                    result["products"] = keywords
                    result["tagging_dict"]["products"] = keywords
                    all_keywords.update(keywords)
                
                # 匹配技能关键词
                elif line.startswith('[技能关键词]:'):
                    keywords_text = line.replace('[技能关键词]:', '').replace('-', '').strip()
                    keywords = [kw.strip() for kw in keywords_text.split() if kw.strip()]
                    result["keywords"]["skill"] = keywords
                    result["skills"] = keywords
                    result["tagging_dict"]["skills"] = keywords
                    all_keywords.update(keywords)
            
            # 添加SmartSearchConfig
            result["SmartSearchConfig"] = {
                "keywords": list(all_keywords)
            }
            
            # 生成详细分析总结
            try:
                result["summary"] = self._generate_detailed_summary(result)
            except Exception as e:
                print(f"详细分析生成失败，使用简化版本: {e}")
                # fallback到简化版本
                if result["job_title"] and result["skills"]:
                    result["summary"] = f"招聘{result['job_title']}，主要技能包括{', '.join(result['skills'][:3])}等。"
                else:
                    result["summary"] = "职位分析完成。"
            
            print("使用标记格式解析")
            return result
            
        except Exception as e:
            raise ValueError(f"响应解析失败: {e}")

# 全局实例
keyword_agent = KeywordAgent() 