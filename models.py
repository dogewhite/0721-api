from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, Float, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
from config_loader import config_loader
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

# 使用统一的数据库引擎（避免循环导入，延迟导入）
def get_engine():
    from database import engine
    return engine

def get_session_local():
    from database import SessionLocal
    return SessionLocal

class JD(Base):
    """JD文档表"""
    __tablename__ = "jds"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, comment="职位名称")
    content = Column(Text, nullable=False, comment="JD内容")
    supplementary_info = Column(Text, comment="补充说明")
    
    # 分析结果
    skills = Column(JSON, comment="技能要求列表")
    products = Column(JSON, comment="产品/技术列表")
    companies = Column(JSON, comment="相关企业列表")
    keywords = Column(JSON, comment="关键词组合")
    mermaid_code = Column(Text, comment="Mermaid源码")
    diagram_path = Column(String(500), comment="导图PNG路径")
    summary = Column(Text, comment="岗位总结")
    
    # 文件路径
    jd_file_path = Column(String(500), comment="JD文件OSS路径")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Candidate(Base):
    """候选人表"""
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    jd_id = Column(Integer, nullable=False, comment="关联的JD ID")
    name = Column(String(100), nullable=False, comment="候选人姓名")
    level = Column(String(10), nullable=False, comment="级别 L1/L1.5/L2/L3")
    score = Column(Float, comment="匹配度评分")
    
    # 分析结果
    swot_analysis = Column(JSON, comment="SWOT分析结果")
    summary = Column(Text, comment="人才总结")
    
    # 联系信息
    contact_info = Column(String(255), comment="联系方式")
    resume_path = Column(String(500), comment="简历OSS路径")
    
    # RPA状态
    rpa_status = Column(String(50), default="pending", comment="RPA发送状态")
    message_sent_at = Column(DateTime, comment="消息发送时间")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CommunicationLog(Base):
    """沟通记录表"""
    __tablename__ = "communication_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, comment="候选人ID")
    jd_id = Column(Integer, nullable=False, comment="JD ID")
    
    # 话术内容
    greeting_message = Column(Text, comment="生成的话术")
    custom_message = Column(Text, comment="自定义话术")
    
    # 发送状态
    status = Column(String(50), default="pending", comment="发送状态")
    sent_at = Column(DateTime, comment="发送时间")
    response_received = Column(Boolean, default=False, comment="是否收到回复")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)

# 公司表
class Company(Base):
    __tablename__ = "companies"
    __table_args__ = {"schema": "project_management"}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="公司名称")
    description = Column(Text, comment="公司描述")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    projects = relationship("Project", back_populates="company", cascade="all, delete-orphan")

# 招聘项目表
class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "project_management"}
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="项目名称")
    description = Column(Text, comment="项目描述")
    status = Column(String(50), default="active", comment="项目状态")
    company_id = Column(Integer, ForeignKey("project_management.companies.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    company = relationship("Company", back_populates="projects")
    positions = relationship("Position", back_populates="project", cascade="all, delete-orphan")

# 职位表
class Position(Base):
    __tablename__ = "positions"
    __table_args__ = {"schema": "project_management"}
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project_management.projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, comment="职位名称")
    description = Column(Text, comment="职位描述")
    requirements = Column(Text, comment="职位要求")
    status = Column(String(50), default="active", comment="职位状态")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    project = relationship("Project", back_populates="positions")

# 职位-候选人关联表
class PositionCandidate(Base):
    __tablename__ = "position_candidates"
    __table_args__ = {"schema": "project_management"}
    
    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("project_management.positions.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)  # 引用public schema的resumes表
    status = Column(String(50), default="pending", comment="状态")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关联关系
    position = relationship("Position")
    resume = relationship("Resume", back_populates="position_candidates")

# 更新Resume模型，添加与职位的关联
class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    gender = Column(String)
    age = Column(Integer)
    education = Column(String)
    work_experience = Column(String)
    skills = Column(String)
    contact = Column(String)
    source = Column(String)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 添加关联关系
    position_candidates = relationship("PositionCandidate", back_populates="resume")

# 用户表（auth.users）
class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

# 创建所有表
def create_tables():
    Base.metadata.create_all(bind=get_engine())

# 获取数据库会话
def get_db():
    db = get_session_local()
    try:
        yield db
    finally:
        db.close() 