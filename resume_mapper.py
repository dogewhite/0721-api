#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, date
from typing import Dict, Any, List, Optional
from talent_models import Resume, WorkExperience, EducationExperience, ProjectExperience
from draft_models import DraftResume, DraftWorkExperience, DraftEducationExperience, DraftProjectExperience
import json

class ResumeMapper:
    """简历数据映射器"""
    
    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        try:
            # 尝试多种日期格式
            formats = [
                '%Y-%m-%d',
                '%Y/%m/%d',
                '%Y年%m月%d日',
                '%Y.%m.%d'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    @staticmethod
    def map_liepin_plugin_data(plugin_json_data: Dict[str, Any]) -> Resume:
        """将猎聘Chrome插件的JSON数据映射到Resume对象"""
        resume = Resume()
        
        # 处理插件的数据结构 - 插件输出的是数组格式，取第一个元素
        if isinstance(plugin_json_data, list) and len(plugin_json_data) > 0:
            data = plugin_json_data[0]
        else:
            data = plugin_json_data
        
        # 基本信息映射 (1.基本信息)
        basic_info = data.get('1.基本信息', {})
        resume.chinese_name = basic_info.get('姓名')
        resume.gender = basic_info.get('性别')
        
        # 解析年龄
        age_str = basic_info.get('年龄', '')
        if age_str and '岁' in age_str:
            try:
                age = int(age_str.replace('岁', ''))
                # 根据年龄估算出生年份
                current_year = datetime.now().year
                estimated_birth_year = current_year - age
                resume.birth_date = date(estimated_birth_year, 1, 1)
            except:
                pass
        
        resume.current_city = basic_info.get('地区')
        
        # 解析工作年限
        work_years_str = basic_info.get('工作年限', '')
        if work_years_str and '年' in work_years_str:
            try:
                years = int(work_years_str.replace('年', ''))
                resume.summary_total_years = years
            except:
                pass
        
        # 当前职位和公司
        resume.expected_position = basic_info.get('职位')
        
        # 求职意向映射 (2.求职意向)
        job_intention = data.get('2.求职意向', {})
        resume.expected_position = resume.expected_position or job_intention.get('期望职位')
        resume.expected_cities = [job_intention.get('期望地区')] if job_intention.get('期望地区') else []
        resume.expected_salary_monthly = job_intention.get('期望薪资')
        
        # 技能标签映射 (8.技能)
        skills = data.get('8.技能', [])
        if isinstance(skills, list):
            resume.skills = skills
        elif isinstance(skills, str):
            resume.skills = [skills]
        
        # 语言能力映射 (7.语言能力)
        languages = data.get('7.语言能力', [])
        if isinstance(languages, list):
            resume.languages = []
            for lang in languages:
                if isinstance(lang, dict):
                    lang_name = lang.get('语言', '')
                    lang_level = lang.get('水平', '')
                    if lang_name:
                        resume.languages.append(f"{lang_name}: {lang_level}")
                elif isinstance(lang, str):
                    resume.languages.append(lang)
        
        # 自我评价映射 (9.自我评价)
        self_evaluation = data.get('9.自我评价', '')
        if self_evaluation:
            resume.ai_profile = self_evaluation
        
        # 总体信息映射 (0.总体信息)
        general_info = data.get('0.总体信息', {})
        resume.avatar_url = general_info.get('头像')
        resume.resume_number = general_info.get('简历编号')
        
        # 基本信息中的方便联系时间
        resume.contact_time_preference = basic_info.get('方便联系时间')
        
        return resume
    
    @staticmethod
    def map_liepin_work_experiences(plugin_json_data: Dict[str, Any], resume_id: int) -> List[WorkExperience]:
        """将猎聘插件的工作经历数据映射到WorkExperience对象列表"""
        work_experiences = []
        
        # 处理插件的数据结构
        if isinstance(plugin_json_data, list) and len(plugin_json_data) > 0:
            data = plugin_json_data[0]
        else:
            data = plugin_json_data
        
        work_data_list = data.get('3.工作经历', [])
        
        for work_data in work_data_list:
            work_exp = WorkExperience()
            work_exp.resume_id = resume_id
            
            # 公司名称
            work_exp.company_name = work_data.get('公司名称')
            
            # 解析工作时间
            work_time = work_data.get('工作时间', '')
            if work_time:
                # 处理时间格式，如 "2020.03-至今" 或 "2020.03-2023.12"
                time_parts = work_time.split('-')
                if len(time_parts) >= 2:
                    start_time = time_parts[0].strip()
                    end_time = time_parts[1].strip()
                    
                    # 解析开始时间
                    if start_time and start_time != '至今':
                        try:
                            # 处理 "2020.03" 格式
                            if '.' in start_time:
                                year, month = start_time.split('.')
                                work_exp.start_date = date(int(year), int(month), 1)
                        except:
                            pass
                    
                    # 解析结束时间
                    if end_time and end_time != '至今':
                        try:
                            if '.' in end_time:
                                year, month = end_time.split('.')
                                work_exp.end_date = date(int(year), int(month), 1)
                        except:
                            pass
                    
                    # 设置当前状态
                    if end_time == '至今':
                        work_exp.current_status = '在职'
                    else:
                        work_exp.current_status = '离职'
            
            # 职位信息
            work_exp.position = work_data.get('职位名称')
            work_exp.department = work_data.get('所在部门')
            work_exp.report_to = work_data.get('汇报对象')
            work_exp.subordinates = work_data.get('下属人数')
            
            # 工作描述和业绩
            work_exp.job_description = work_data.get('职责业绩')
            
            # 公司信息
            work_exp.company_location = work_data.get('工作地点')
            work_exp.company_intro = work_data.get('公司介绍')
            
            # 企业信息
            company_info = work_data.get('企业信息', '')
            company_type = work_data.get('所属行业', '')
            company_tags = work_data.get('企业标签', [])
            
            if company_info:
                work_exp.company_type = company_info
            if company_type:
                work_exp.company_stage = company_type
            
            work_experiences.append(work_exp)
        
        return work_experiences
    
    @staticmethod
    def map_liepin_education_experiences(plugin_json_data: Dict[str, Any], resume_id: int) -> List[EducationExperience]:
        """将猎聘插件的教育经历数据映射到EducationExperience对象列表"""
        education_experiences = []
        
        # 处理插件的数据结构
        if isinstance(plugin_json_data, list) and len(plugin_json_data) > 0:
            data = plugin_json_data[0]
        else:
            data = plugin_json_data
        
        education_data_list = data.get('5.教育经历', [])
        
        for education_data in education_data_list:
            edu_exp = EducationExperience()
            edu_exp.resume_id = resume_id
            
            edu_exp.school = education_data.get('学校名称')
            edu_exp.major = education_data.get('专业名称')
            edu_exp.degree = education_data.get('学位')
            
            # 解析就读时间
            study_time = education_data.get('就读时间', '')
            if study_time:
                time_parts = study_time.split('-')
                if len(time_parts) >= 2:
                    start_time = time_parts[0].strip()
                    end_time = time_parts[1].strip()
                    
                    try:
                        if start_time and '.' in start_time:
                            year, month = start_time.split('.')
                            edu_exp.start_date = date(int(year), int(month), 1)
                        if end_time and '.' in end_time:
                            year, month = end_time.split('.')
                            edu_exp.end_date = date(int(year), int(month), 1)
                    except:
                        pass
            
            education_experiences.append(edu_exp)
        
        return education_experiences
    
    @staticmethod
    def map_liepin_project_experiences(plugin_json_data: Dict[str, Any], resume_id: int) -> List[ProjectExperience]:
        """将猎聘插件的项目经历数据映射到ProjectExperience对象列表"""
        project_experiences = []
        
        # 处理插件的数据结构
        if isinstance(plugin_json_data, list) and len(plugin_json_data) > 0:
            data = plugin_json_data[0]
        else:
            data = plugin_json_data
        
        project_data_list = data.get('4.项目经历', [])
        
        for project_data in project_data_list:
            proj_exp = ProjectExperience()
            proj_exp.resume_id = resume_id
            
            proj_exp.project_name = project_data.get('项目名称')
            proj_exp.role = project_data.get('项目职务')
            
            # 解析项目时间
            project_time = project_data.get('项目时间', '')
            if project_time:
                time_parts = project_time.split('-')
                if len(time_parts) >= 2:
                    start_time = time_parts[0].strip()
                    end_time = time_parts[1].strip()
                    
                    try:
                        if start_time and '.' in start_time:
                            year, month = start_time.split('.')
                            proj_exp.start_date = date(int(year), int(month), 1)
                        if end_time and '.' in end_time:
                            year, month = end_time.split('.')
                            proj_exp.end_date = date(int(year), int(month), 1)
                    except:
                        pass
            
            proj_exp.project_intro = project_data.get('项目描述')
            proj_exp.project_achievements = project_data.get('项目业绩')
            
            project_experiences.append(proj_exp)
        
        return project_experiences
    
    @staticmethod
    def map_liepin_json_to_resume(plugin_json_data: Dict[str, Any]) -> tuple[Resume, List[WorkExperience], List[EducationExperience], List[ProjectExperience]]:
        """将猎聘插件的完整JSON数据映射到所有相关对象"""
        # 映射主简历数据
        resume = ResumeMapper.map_liepin_plugin_data(plugin_json_data)
        
        # 映射工作经历
        work_experiences = ResumeMapper.map_liepin_work_experiences(plugin_json_data, resume.id)
        
        # 映射教育经历
        education_experiences = ResumeMapper.map_liepin_education_experiences(plugin_json_data, resume.id)
        
        # 映射项目经历
        project_experiences = ResumeMapper.map_liepin_project_experiences(plugin_json_data, resume.id)
        
        return resume, work_experiences, education_experiences, project_experiences

    @staticmethod
    def map_resume_data(json_data: Dict[str, Any]) -> Resume:
        """将JSON数据映射到Resume对象"""
        resume = Resume()
        
        # 基本信息映射
        basic_info = json_data.get('basic_info', {})
        resume.chinese_name = basic_info.get('chinese_name')
        resume.english_name = basic_info.get('english_name')
        resume.gender = basic_info.get('gender')
        resume.birth_date = ResumeMapper.parse_date(basic_info.get('birth_date'))
        resume.native_place = basic_info.get('native_place')
        resume.current_city = basic_info.get('current_city')
        resume.political_status = basic_info.get('political_status')
        resume.marital_status = basic_info.get('marital_status')
        resume.health = basic_info.get('health')
        resume.height_cm = basic_info.get('height_cm')
        resume.weight_kg = basic_info.get('weight_kg')
        resume.personality = basic_info.get('personality')
        
        # 联系方式映射
        contact_info = json_data.get('contact_info', {})
        resume.phone = contact_info.get('phone')
        resume.email = contact_info.get('email')
        resume.wechat = contact_info.get('wechat')
        
        # 职业总结映射
        summary = json_data.get('summary', {})
        resume.summary_total_years = summary.get('total_years')
        resume.summary_industries = summary.get('industries', [])
        resume.summary_roles = summary.get('roles', [])
        resume.skills = summary.get('skills', [])
        resume.awards = summary.get('awards', [])
        resume.languages = summary.get('languages', [])
        resume.highest_education = summary.get('highest_education')
        
        # 期望信息映射
        expectations = json_data.get('expectations', {})
        resume.expected_location_range_km = expectations.get('location_range_km')
        resume.expected_cities = expectations.get('cities', [])
        resume.expected_salary_yearly = expectations.get('salary_yearly')
        resume.expected_salary_monthly = expectations.get('salary_monthly')
        resume.expected_industries = expectations.get('industries', [])
        resume.expected_company_nature = expectations.get('company_nature')
        resume.expected_company_size = expectations.get('company_size')
        resume.expected_company_stage = expectations.get('company_stage')
        resume.expected_position = expectations.get('position')
        resume.additional_conditions = expectations.get('additional_conditions')
        resume.job_search_status = expectations.get('job_search_status')
        
        # AI分析结果映射
        ai_analysis = json_data.get('ai_analysis', {})
        resume.ai_profile = ai_analysis.get('profile')
        resume.ai_swot = ai_analysis.get('swot')
        resume.ai_career_stage = ai_analysis.get('career_stage')
        resume.ai_personality = ai_analysis.get('personality')
        
        return resume
    
    @staticmethod
    def map_work_experiences(json_data: Dict[str, Any], resume_id: int) -> List[WorkExperience]:
        """将工作经历JSON数据映射到WorkExperience对象列表"""
        work_experiences = []
        work_data_list = json_data.get('work_experiences', [])
        
        for work_data in work_data_list:
            work_exp = WorkExperience()
            work_exp.resume_id = resume_id
            
            # 公司信息
            company_info = work_data.get('company_info', {})
            work_exp.company_name = company_info.get('name')
            work_exp.company_intro = company_info.get('intro')
            work_exp.company_size = company_info.get('size')
            work_exp.company_valuation = company_info.get('valuation')
            work_exp.company_type = company_info.get('type')
            work_exp.company_stage = company_info.get('stage')
            work_exp.company_location = company_info.get('location')
            
            # 工作信息
            work_exp.start_date = ResumeMapper.parse_date(work_data.get('start_date'))
            work_exp.end_date = ResumeMapper.parse_date(work_data.get('end_date'))
            work_exp.current_status = work_data.get('current_status')
            work_exp.position = work_data.get('position')
            work_exp.department = work_data.get('department')
            work_exp.report_to = work_data.get('report_to')
            work_exp.subordinates = work_data.get('subordinates')
            work_exp.job_description = work_data.get('job_description')
            work_exp.job_details = work_data.get('job_details', [])
            work_exp.achievements = work_data.get('achievements', [])
            
            work_experiences.append(work_exp)
        
        return work_experiences
    
    @staticmethod
    def map_education_experiences(json_data: Dict[str, Any], resume_id: int) -> List[EducationExperience]:
        """将教育经历JSON数据映射到EducationExperience对象列表"""
        education_experiences = []
        education_data_list = json_data.get('education_experiences', [])
        
        for education_data in education_data_list:
            edu_exp = EducationExperience()
            edu_exp.resume_id = resume_id
            
            edu_exp.school = education_data.get('school')
            edu_exp.major = education_data.get('major')
            edu_exp.degree = education_data.get('degree')
            edu_exp.start_date = ResumeMapper.parse_date(education_data.get('start_date'))
            edu_exp.end_date = ResumeMapper.parse_date(education_data.get('end_date'))
            edu_exp.main_courses = education_data.get('main_courses', [])
            edu_exp.certificates = education_data.get('certificates', [])
            edu_exp.ranking = education_data.get('ranking')
            
            education_experiences.append(edu_exp)
        
        return education_experiences
    
    @staticmethod
    def map_project_experiences(json_data: Dict[str, Any], resume_id: int) -> List[ProjectExperience]:
        """将项目经历JSON数据映射到ProjectExperience对象列表"""
        project_experiences = []
        project_data_list = json_data.get('project_experiences', [])
        
        for project_data in project_data_list:
            proj_exp = ProjectExperience()
            proj_exp.resume_id = resume_id
            
            proj_exp.project_name = project_data.get('project_name')
            proj_exp.start_date = ResumeMapper.parse_date(project_data.get('start_date'))
            proj_exp.end_date = ResumeMapper.parse_date(project_data.get('end_date'))
            proj_exp.role = project_data.get('role')
            proj_exp.project_intro = project_data.get('project_intro')
            proj_exp.project_achievements = project_data.get('project_achievements')
            
            project_experiences.append(proj_exp)
        
        return project_experiences
    
    @staticmethod
    def map_json_to_resume(json_data: Dict[str, Any]) -> tuple[Resume, List[WorkExperience], List[EducationExperience], List[ProjectExperience]]:
        """将完整的JSON数据映射到所有相关对象"""
        # 映射主简历数据
        resume = ResumeMapper.map_resume_data(json_data)
        
        # 映射工作经历
        work_experiences = ResumeMapper.map_work_experiences(json_data, resume.id)
        
        # 映射教育经历
        education_experiences = ResumeMapper.map_education_experiences(json_data, resume.id)
        
        # 映射项目经历
        project_experiences = ResumeMapper.map_project_experiences(json_data, resume.id)
        
        return resume, work_experiences, education_experiences, project_experiences
    
    @staticmethod
    def map_json_to_draft_resume(json_data: Dict[str, Any]) -> tuple[DraftResume, List[DraftWorkExperience], List[DraftEducationExperience], List[DraftProjectExperience]]:
        """将JSON数据映射到DraftResume对象"""
        draft_resume = DraftResume()
        
        # 基本信息映射
        basic_info = json_data.get('basic_info', {})
        draft_resume.resume_number = basic_info.get('resume_number')
        draft_resume.contact_time_preference = basic_info.get('contact_time_preference')
        draft_resume.chinese_name = basic_info.get('chinese_name')
        draft_resume.english_name = basic_info.get('english_name')
        draft_resume.gender = basic_info.get('gender')
        draft_resume.birth_date = ResumeMapper.parse_date(basic_info.get('birth_date'))
        draft_resume.native_place = basic_info.get('native_place')
        draft_resume.current_city = basic_info.get('current_city')
        draft_resume.political_status = basic_info.get('political_status')
        draft_resume.marital_status = basic_info.get('marital_status')
        draft_resume.health = basic_info.get('health')
        draft_resume.height_cm = basic_info.get('height_cm')
        draft_resume.weight_kg = basic_info.get('weight_kg')
        draft_resume.personality = basic_info.get('personality')
        
        # 联系方式映射
        contact_info = json_data.get('contact_info', {})
        draft_resume.phone = contact_info.get('phone')
        draft_resume.email = contact_info.get('email')
        draft_resume.wechat = contact_info.get('wechat')
        
        # 职业总结映射
        summary = json_data.get('summary', {})
        draft_resume.summary_total_years = summary.get('total_years')
        draft_resume.summary_industries = summary.get('industries', [])
        draft_resume.summary_roles = summary.get('roles', [])
        draft_resume.skills = summary.get('skills', [])
        draft_resume.awards = summary.get('awards', [])
        draft_resume.languages = summary.get('languages', [])
        draft_resume.highest_education = summary.get('highest_education')
        
        # 期望信息映射
        expectations = json_data.get('expectations', {})
        draft_resume.expected_location_range_km = expectations.get('location_range_km')
        draft_resume.expected_cities = expectations.get('cities', [])
        draft_resume.expected_salary_yearly = expectations.get('salary_yearly')
        draft_resume.expected_salary_monthly = expectations.get('salary_monthly')
        draft_resume.expected_industries = expectations.get('industries', [])
        draft_resume.expected_company_nature = expectations.get('company_nature')
        draft_resume.expected_company_size = expectations.get('company_size')
        draft_resume.expected_company_stage = expectations.get('company_stage')
        draft_resume.expected_position = expectations.get('position')
        draft_resume.additional_conditions = expectations.get('additional_conditions')
        draft_resume.job_search_status = expectations.get('job_search_status')
        
        # AI分析结果映射
        ai_analysis = json_data.get('ai_analysis', {})
        draft_resume.ai_profile = ai_analysis.get('profile')
        draft_resume.ai_swot = ai_analysis.get('swot')
        draft_resume.ai_career_stage = ai_analysis.get('career_stage')
        draft_resume.ai_personality = ai_analysis.get('personality')
        
        # 追溯信息映射
        trace_info = json_data.get('trace_info', {})
        draft_resume.avatar_url = trace_info.get('avatar_url')
        
        # 工作经历映射
        draft_work_experiences = []
        for work_data in json_data.get('work_experiences', []):
            work_exp = DraftWorkExperience()
            work_exp.company_name = work_data.get('company_name')
            work_exp.company_intro = work_data.get('company_intro')
            work_exp.company_size = work_data.get('company_size')
            work_exp.company_valuation = work_data.get('company_valuation')
            work_exp.company_type = work_data.get('company_type')
            work_exp.company_stage = work_data.get('company_stage')
            work_exp.company_location = work_data.get('company_location')
            work_exp.start_date = ResumeMapper.parse_date(work_data.get('start_date'))
            work_exp.end_date = ResumeMapper.parse_date(work_data.get('end_date'))
            work_exp.current_status = work_data.get('current_status')
            work_exp.position = work_data.get('position')
            work_exp.department = work_data.get('department')
            work_exp.report_to = work_data.get('report_to')
            work_exp.subordinates = work_data.get('subordinates')
            work_exp.job_description = work_data.get('job_description')
            work_exp.job_details = work_data.get('job_details', [])
            work_exp.achievements = work_data.get('achievements', [])
            draft_work_experiences.append(work_exp)
        
        # 教育经历映射
        draft_education_experiences = []
        for edu_data in json_data.get('education_experiences', []):
            edu_exp = DraftEducationExperience()
            edu_exp.school = edu_data.get('school')
            edu_exp.major = edu_data.get('major')
            edu_exp.degree = edu_data.get('degree')
            edu_exp.start_date = ResumeMapper.parse_date(edu_data.get('start_date'))
            edu_exp.end_date = ResumeMapper.parse_date(edu_data.get('end_date'))
            edu_exp.main_courses = edu_data.get('main_courses', [])
            edu_exp.certificates = edu_data.get('certificates', [])
            edu_exp.ranking = edu_data.get('ranking')
            draft_education_experiences.append(edu_exp)
        
        # 项目经历映射
        draft_project_experiences = []
        for proj_data in json_data.get('project_experiences', []):
            proj_exp = DraftProjectExperience()
            proj_exp.project_name = proj_data.get('project_name')
            proj_exp.start_date = ResumeMapper.parse_date(proj_data.get('start_date'))
            proj_exp.end_date = ResumeMapper.parse_date(proj_data.get('end_date'))
            proj_exp.role = proj_data.get('role')
            proj_exp.project_intro = proj_data.get('project_intro')
            proj_exp.project_achievements = proj_data.get('project_achievements')
            draft_project_experiences.append(proj_exp)
        
        return draft_resume, draft_work_experiences, draft_education_experiences, draft_project_experiences

# 示例JSON数据结构
SAMPLE_RESUME_JSON = {
    "basic_info": {
        "chinese_name": "张三",
        "english_name": "Zhang San",
        "gender": "男",
        "birth_date": "1990-01-01",
        "native_place": "北京",
        "current_city": "上海",
        "political_status": "群众",
        "marital_status": "未婚",
        "health": "良好",
        "height_cm": 175,
        "weight_kg": 70,
        "personality": "开朗"
    },
    "contact_info": {
        "phone": "13800138000",
        "email": "zhangsan@example.com",
        "wechat": "zhangsan123"
    },
    "summary": {
        "total_years": 5,
        "industries": ["互联网", "金融"],
        "roles": ["前端开发", "全栈开发"],
        "skills": ["JavaScript", "React", "Vue", "Node.js"],
        "awards": ["优秀员工", "技术创新奖"],
        "languages": ["英语: 流利", "日语: 基础"]
    },
    "expectations": {
        "location_range_km": 50,
        "cities": ["上海", "北京"],
        "salary_yearly": 300000,
        "salary_monthly": 25000,
        "industries": ["互联网", "金融科技"],
        "company_nature": "民营企业",
        "company_size": "500-1000人",
        "company_stage": "B轮",
        "position": "高级前端工程师",
        "additional_conditions": "希望有期权激励",
        "job_search_status": "在职找工作"
    },
    "ai_analysis": {
        "profile": "具有5年前端开发经验，技术栈全面，有良好的团队协作能力",
        "swot": "优势：技术扎实，学习能力强；劣势：管理经验不足",
        "career_stage": "成长期",
        "personality": "技术导向，注重细节"
    },
    "work_experiences": [
        {
            "company_info": {
                "name": "某互联网公司",
                "intro": "专注于移动互联网应用开发",
                "size": "500-1000人",
                "valuation": "10亿",
                "type": "民营企业",
                "stage": "C轮",
                "location": "上海"
            },
            "start_date": "2020-03-01",
            "end_date": None,
            "current_status": "在职",
            "position": "高级前端工程师",
            "department": "技术部",
            "report_to": "技术总监",
            "subordinates": "3人",
            "job_description": "负责公司核心产品的前端架构设计和开发",
            "job_details": [
                "设计并实现响应式前端架构",
                "优化前端性能，提升用户体验",
                "指导初级开发人员"
            ],
            "achievements": [
                "主导完成公司核心产品重构，性能提升50%",
                "获得年度优秀员工称号"
            ]
        }
    ],
    "education_experiences": [
        {
            "school": "某大学",
            "major": "计算机科学与技术",
            "degree": "本科",
            "start_date": "2016-09-01",
            "end_date": "2020-06-30",
            "main_courses": ["数据结构", "算法设计", "软件工程"],
            "certificates": ["计算机等级证书"],
            "ranking": "前20%"
        }
    ],
    "project_experiences": [
        {
            "project_name": "企业管理系统重构",
            "start_date": "2022-01-01",
            "end_date": "2022-06-30",
            "role": "前端负责人",
            "project_intro": "对公司内部管理系统进行全面重构",
            "project_achievements": "系统响应速度提升60%，用户满意度显著提高"
        }
    ]
}

# 猎聘插件JSON数据示例
SAMPLE_LIEPIN_PLUGIN_JSON = [
    {
        "0.总体信息": {
            "简历编号": "123456",
            "页面URL": "https://www.liepin.com/resume/123456",
            "提取时间": "2024-01-01 12:00:00",
            "登录时间": "最后登录：1天前",
            "头像": "https://example.com/avatar.jpg",
            "活跃度": "在线"
        },
        "1.基本信息": {
            "姓名": "张三",
            "性别": "男",
            "年龄": "28岁",
            "学历": "本科",
            "工作年限": "5年",
            "现居地": "北京",
            "电话": "138****1234",
            "邮箱": "example@email.com",
            "职位": "前端开发工程师",
            "公司": "某科技公司"
        },
        "2.求职意向": {
            "期望职位": "前端开发工程师",
            "期望薪资": "15-25K",
            "期望城市": "北京",
            "工作性质": "全职"
        },
        "3.工作经历": [
            {
                "时间段": "2020.03-至今",
                "公司名称": "某科技公司",
                "职位名称": "高级前端工程师",
                "工作描述": "负责前端架构设计...",
                "所属行业": "互联网/移动互联网",
                "企业信息": "A轮 / 100-499人",
                "企业标签": ["技术驱动", "成长速度快"],
                "所在部门": "技术部",
                "工作地点": "北京",
                "下属人数": "3人",
                "汇报对象": "技术总监",
                "职责业绩": "负责公司核心产品的前端架构设计和开发，优化前端性能，提升用户体验",
                "公司介绍": "专注于移动互联网应用开发"
            }
        ],
        "4.项目经历": [
            {
                "项目时间": "2022.01-2022.06",
                "项目名称": "企业管理系统重构",
                "项目职务": "前端负责人",
                "所在公司": "某科技公司",
                "项目描述": "对公司内部管理系统进行全面重构",
                "项目职责": "负责前端架构设计和核心功能开发",
                "项目业绩": "系统响应速度提升60%，用户满意度显著提高"
            }
        ],
        "5.教育经历": [
            {
                "学校标志": "https://example.com/school-logo.jpg",
                "学校名称": "某大学",
                "专业名称": "计算机科学与技术",
                "学位": "本科",
                "就读时间": "2016.09-2020.06",
                "学校标签1": "985",
                "学校标签2": "211",
                "学校标签3": ""
            }
        ],
        "6.资格证书": ["计算机等级证书", "前端开发工程师证书"],
        "7.语言能力": [
            {
                "语言": "英语",
                "水平": "流利"
            },
            {
                "语言": "日语",
                "水平": "基础"
            }
        ],
        "8.技能标签": ["JavaScript", "React", "Vue", "Node.js"],
        "9.自我评价": "具有丰富的前端开发经验，技术栈全面，有良好的团队协作能力，注重代码质量和用户体验。",
        "10.附加信息": "获得年度优秀员工称号，参与开源项目贡献。"
    }
] 