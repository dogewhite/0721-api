from sqlalchemy import Column, Integer, String, Text, Date, DateTime, JSON, ForeignKey, ARRAY, Float, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config_loader import config_loader
from sqlalchemy.dialects.postgresql import UUID
import uuid

# 创建draft schema的Base
DraftBase = declarative_base()

# 创建talentdb连接
talentdb_engine = create_engine(config_loader.get_talentdb_url())
DraftDBSession = sessionmaker(autocommit=False, autoflush=False, bind=talentdb_engine)

class DraftResume(DraftBase):
    """简历草稿主表 - 用于暂存待确认的简历数据"""
    __tablename__ = "draft_resumes"
    __table_args__ = {"schema": "draft"}
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 用户隔离字段
    user_id = Column(UUID(as_uuid=True), nullable=False, comment="上传用户ID")
    
    # 简历标识信息
    resume_number = Column(Text, comment="简历编号")
    contact_time_preference = Column(Text, comment="方便联系时间")
    
    # 基本信息
    chinese_name = Column(Text, comment="中文姓名")
    english_name = Column(Text, comment="英文姓名")
    gender = Column(Text, comment="性别")
    birth_date = Column(Date, comment="出生日期")
    native_place = Column(Text, comment="籍贯")
    current_city = Column(Text, comment="现居城市")
    political_status = Column(Text, comment="政治面貌")
    marital_status = Column(Text, comment="婚姻状况")
    health = Column(Text, comment="健康状况")
    height_cm = Column(Text, comment="身高(cm)")
    weight_kg = Column(Text, comment="体重(kg)")
    personality = Column(Text, comment="性格特点")
    
    # 联系方式
    phone = Column(Text, comment="电话")
    email = Column(Text, comment="邮箱")
    wechat = Column(Text, comment="微信")
    
    # 职业总结
    summary_total_years = Column(Text, comment="工作年限")
    summary_industries = Column(ARRAY(Text), comment="行业经验")
    summary_roles = Column(ARRAY(Text), comment="角色经验")
    skills = Column(ARRAY(Text), comment="技能")
    awards = Column(ARRAY(Text), comment="获奖情况")
    languages = Column(ARRAY(Text), comment="语言能力")
    highest_education = Column(Text, comment="最高学历")
    
    # 期望信息
    expected_location_range_km = Column(Text, comment="期望工作地点范围(公里)")
    expected_cities = Column(ARRAY(Text), comment="期望城市")
    expected_salary_yearly = Column(Text, comment="期望年薪")
    expected_salary_monthly = Column(Text, comment="期望月薪")
    expected_industries = Column(ARRAY(Text), comment="期望行业")
    expected_company_nature = Column(Text, comment="期望公司性质")
    expected_company_size = Column(Text, comment="期望公司规模")
    expected_company_stage = Column(Text, comment="期望公司阶段")
    expected_position = Column(Text, comment="期望职位")
    additional_conditions = Column(Text, comment="其他条件")
    job_search_status = Column(Text, comment="求职状态")
    
    # AI分析结果
    ai_profile = Column(Text, comment="AI生成的个人简介")
    ai_swot = Column(JSON, comment="AI生成的SWOT分析")
    ai_career_stage = Column(Text, comment="AI判断的职业阶段")
    ai_personality = Column(Text, comment="AI分析的性格特点")
    
    # 追溯信息
    oss_path = Column(Text, comment="OSS存储路径")
    oss_url = Column(Text, comment="OSS访问URL")
    original_filename = Column(Text, comment="原始文件名")
    file_format = Column(Text, comment="文件格式类型")
    upload_source = Column(Text, comment="上传来源")
    avatar_url = Column(Text, comment="头像URL")
    
    # 草稿特有字段
    kimi_file_id = Column(Text, comment="Kimi文件ID")
    draft_status = Column(Text, default="pending_review", comment="草稿状态")
    review_notes = Column(Text, comment="审核备注")
    
    # 岗位关联字段
    position_id = Column(Integer, comment="关联的岗位ID")
    position_name = Column(Text, comment="岗位名称")
    project_id = Column(Integer, comment="关联的项目ID")
    project_name = Column(Text, comment="项目名称")
    company_id = Column(Integer, comment="关联的公司ID")
    company_name = Column(Text, comment="公司名称")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    work_experiences = relationship("DraftWorkExperience", back_populates="resume", cascade="all, delete-orphan")
    education_experiences = relationship("DraftEducationExperience", back_populates="resume", cascade="all, delete-orphan")
    project_experiences = relationship("DraftProjectExperience", back_populates="resume", cascade="all, delete-orphan")
    # status = relationship("DraftResumeStatus", back_populates="resume", uselist=False)  # 暂时注释掉

class DraftWorkExperience(DraftBase):
    """工作经历草稿表"""
    __tablename__ = "draft_work_experiences"
    __table_args__ = {"schema": "draft"}
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("draft.draft_resumes.id", ondelete="CASCADE"), comment="关联的简历草稿ID")
    
    # 公司信息
    company_name = Column(Text, comment="公司名称")
    company_intro = Column(Text, comment="公司简介")
    company_size = Column(Text, comment="公司规模")
    company_valuation = Column(Text, comment="公司估值")
    company_type = Column(Text, comment="公司类型")
    company_stage = Column(Text, comment="公司阶段")
    company_location = Column(Text, comment="公司地点")
    
    # 工作信息
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")
    current_status = Column(Text, comment="当前状态")
    position = Column(Text, comment="职位")
    department = Column(Text, comment="部门")
    report_to = Column(Text, comment="汇报对象")
    subordinates = Column(Text, comment="下属人数")
    job_description = Column(Text, comment="工作描述")
    job_details = Column(ARRAY(Text), comment="工作详情")
    achievements = Column(ARRAY(Text), comment="工作成就")
    
    # 关联关系
    resume = relationship("DraftResume", back_populates="work_experiences")

class DraftEducationExperience(DraftBase):
    """教育经历草稿表"""
    __tablename__ = "draft_education_experiences"
    __table_args__ = {"schema": "draft"}
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("draft.draft_resumes.id", ondelete="CASCADE"), comment="关联的简历草稿ID")
    
    # 学校信息
    school = Column(Text, comment="学校名称")
    major = Column(Text, comment="专业")
    degree = Column(Text, comment="学位")
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")
    main_courses = Column(ARRAY(Text), comment="主要课程")
    certificates = Column(ARRAY(Text), comment="证书")
    ranking = Column(Text, comment="排名")
    
    # 关联关系
    resume = relationship("DraftResume", back_populates="education_experiences")

class DraftProjectExperience(DraftBase):
    """项目经历草稿表"""
    __tablename__ = "draft_project_experiences"
    __table_args__ = {"schema": "draft"}
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("draft.draft_resumes.id", ondelete="CASCADE"), comment="关联的简历草稿ID")
    
    # 项目信息
    project_name = Column(Text, comment="项目名称")
    start_date = Column(Date, comment="开始日期")
    end_date = Column(Date, comment="结束日期")
    role = Column(Text, comment="角色")
    project_intro = Column(Text, comment="项目简介")
    project_achievements = Column(Text, comment="项目成就")
    
    # 关联关系
    resume = relationship("DraftResume", back_populates="project_experiences")

# 创建所有draft表
def create_draft_tables():
    """创建draft schema的所有表"""
    # 首先创建schema
    with talentdb_engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS draft"))
        conn.commit()
    
    # 创建表
    DraftBase.metadata.create_all(bind=talentdb_engine)

# 获取draft数据库会话
def get_draft_db():
    db = DraftDBSession()
    try:
        yield db
    finally:
        db.close() 