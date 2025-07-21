from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, Response
import tempfile
import os
from datetime import datetime
from typing import List, Optional, Any
import json
import re
import base64
import requests
import asyncio
import traceback
from sqlalchemy.orm import Session
import uuid
from sqlalchemy import text, func, cast, String
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from models import User
from database import get_db


# 添加PDF和DOC解析库
try:
    import PyPDF2
    import docx
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("警告: PDF/DOC解析库未安装，将使用简化处理")

from config_loader import config_loader
from oss_utils import oss_manager, download_file_from_oss
from models import *
# 先导入状态管理模型，解决循环依赖
# from resume_status_models import DraftResumeStatus, PublicResumeStatus, DraftStatus, PublicStatus, get_status_db
from talent_models import Resume, WorkExperience, EducationExperience, ProjectExperience, get_talentdb
from resume_mapper import ResumeMapper
from kimi_client import KimiClient
from draft_models import DraftResume, DraftWorkExperience, DraftEducationExperience, DraftProjectExperience, get_draft_db
from KeywordAgent import KeywordAgent
from JDMapGenerator import JDMapGenerator
from llm_manager import llm_manager
from database import get_db, init_db
# from resume_status_api import router as status_router  # 暂时注释掉

# 实例化
keyword_agent = KeywordAgent(api_key=config_loader.get_deepseek_api_key())
jd_map_generator = JDMapGenerator()
kimi_client = KimiClient()

# 初始化数据库
# try:
#     init_db()
# except Exception as e:
#     print(f"数据库初始化失败: {e}，将跳过该步骤。")

# 创建FastAPI应用
app = FastAPI(title="智能JD分析API", version="1.0.0")

# 添加CORS中间件，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT配置
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta=None):
    from datetime import datetime, timedelta
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册状态管理路由
# app.include_router(status_router)  # 暂时注释掉

# 创建数据库表 - 注释掉
# create_tables()

PROMPT_FILES = {
    "kroki": "kroki_prompt.txt",
    "keyword": "keyword_prompt.txt",
    "dic": "dic_prompt.txt",
    "greeting": "greeting_prompt.txt",
    "sim": "sim_prompt.txt"
}

# 读取prompt模板
def load_prompt(prompt_name: str) -> str:
    base_path = os.path.abspath(os.path.dirname(__file__))
    path = os.path.join(base_path, PROMPT_FILES[prompt_name])
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

# 文件解析函数
def extract_text_from_file(file_path: str, file_ext: str) -> str:
    """
    从文件中提取文本内容
    """
    try:
        if file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_ext == '.pdf' and PDF_AVAILABLE:
            return extract_text_from_pdf(file_path)
        elif file_ext in ['.doc', '.docx'] and PDF_AVAILABLE:
            return extract_text_from_docx(file_path)
        else:
            return f"文件格式: {file_ext}，内容需要手动解析"
    except Exception as e:
        return f"文件解析失败: {str(e)}"

def extract_text_from_pdf(file_path: str) -> str:
    """
    从PDF文件中提取文本
    """
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        return f"PDF解析失败: {str(e)}"

def extract_text_from_docx(file_path: str) -> str:
    """
    从DOCX文件中提取文本
    """
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        return f"DOCX解析失败: {str(e)}"

@app.get("/")
async def root():
    return {"message": "API服务正在运行"}

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "API服务正常运行"}

@app.post("/api/upload_jd")
async def upload_jd(
    jd_file: UploadFile = File(...),
    supplementary_info: str = Form(""),
    path: str = Form(""),
):
    """
    仅上传JD文件至库，不进行分析
    """
    temp_file_path = ""
    try:
        content = await jd_file.read()
        
        # 使用传入的path构建对象名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"{path}{timestamp}_{jd_file.filename}"
        
        # 上传到OSS 
        oss_url = oss_manager.upload_bytes(content, object_name)
        
        return {
            "success": True,
            "message": "文件已成功上传至库",
            "filename": jd_file.filename,
            "oss_url": oss_url,
            "object_name": object_name
        }
    except Exception as e:
        print(f"上传至库失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"上传至库失败: {str(e)}")

async def stream_jd_analysis(source: str, file_path: str, supplementary_info: str, file: UploadFile, request_id: str | None = None):
    """
    流式分析JD的生成器函数
    """
    temp_file_path = ""
    try:
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # 步骤一: 获取JD文本 (与之前逻辑相同)
        jd_text = ""
        if source == 'local' and file:
            file_ext = os.path.splitext(file.filename)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            jd_text = extract_text_from_file(temp_file_path, file_ext)
        elif source == 'oss' and file_path:
            # 从OSS下载文件
            file_content = download_file_from_oss(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            jd_text = extract_text_from_file(temp_file_path, file_ext)
        else:
            raise HTTPException(status_code=400, detail="无效的请求")
        
        # 步骤二: 提取关键词和总结，并作为第一个事件流式返回
        # 使用 acreate 异步版本（假设glm4_client支持）
        keyword_result = await keyword_agent.extract_keywords_async(jd_text, supplementary_info)
        yield f"event: keywords_result\ndata: {json.dumps({'request_id': request_id, 'payload': keyword_result})}\n\n"
        
        # 步骤三: 生成岗位导图，并作为第二个事件流式返回
        # 使用 acreate 异步版本
        jd_map_result = await jd_map_generator.generate_jd_map_async(keyword_result)
        yield f"event: diagram_result\ndata: {json.dumps({'request_id': request_id, 'payload': jd_map_result})}\n\n"

    except Exception as e:
        error_message = json.dumps({"request_id": request_id, "error": str(e)})
        print(error_message)
        traceback.print_exc()
        yield f"event: error\ndata: {error_message}\n\n"
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        # 步骤四: 发送结束信号
        yield f"event: done\ndata: {json.dumps({'request_id': request_id})}\n\n"

@app.post("/api/analyze_jd_stream")
async def analyze_jd_stream(
    source: str = Form(...),
    file_path: str = Form(None),
    supplementary_info: str = Form(None),
    file: UploadFile = File(None),
    request_id: str = Form(None)
):
    """
    流式分析JD的API端点
    """
    return StreamingResponse(
        stream_jd_analysis(source, file_path, supplementary_info, file, request_id),
        media_type="text/event-stream"
    )

@app.post("/api/preview_file")
async def preview_file(file: UploadFile = File(...)):
    """
    接收文件并返回其文本内容用于预览
    """
    temp_file_path = ""
    try:
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.pdf', '.doc', '.docx', '.txt']:
            raise HTTPException(status_code=400, detail="不支持的文件格式")

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        text_content = extract_text_from_file(temp_file_path, file_ext)
        
        return {"content": text_content}

    except Exception as e:
        print(f"文件预览失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"文件预览失败: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@app.post("/api/oss/preview")
async def preview_oss_file(request: dict):
    """
    从OSS下载文件并返回其文本内容用于预览
    """
    temp_file_path = ""
    try:
        file_path = request.get("file_path")
        if not file_path:
            raise HTTPException(status_code=400, detail="缺少文件路径")

        # 从OSS下载文件 - 暂时注释掉
        file_content = download_file_from_oss(file_path)
        
        if not file_content:
            raise HTTPException(status_code=404, detail="文件不存在或无法访问")

        # # 获取文件扩展名
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in ['.pdf', '.doc', '.docx', '.txt']:
            raise HTTPException(status_code=400, detail="不支持的文件格式")

        # # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        # # 提取文本内容
        text_content = extract_text_from_file(temp_file_path, file_ext)
        
        return {"content": text_content}

    except Exception as e:
        print(f"OSS文件预览失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"OSS文件预览失败: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@app.post("/api/oss/upload")
async def upload_to_oss(
    file: UploadFile = File(...),
    path: str = Form(...)
):
    """
    接收文件并上传到OSS指定路径
    """
    temp_file_path = "" 
    try:
        # 确保路径格式正确
        if path and not path.endswith('/'):
            path += '/'
            
        object_name = f"{path}{file.filename}" if path else file.filename

        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        file_url = oss_manager.upload_file(temp_file_path, object_name)
        
        return {"success": True, "message": f"文件已成功上传到 {object_name}", "url": file_url}

    except Exception as e:
        print(f"上传到OSS失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"上传到OSS失败: {str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@app.post("/api/generate_candidates")
async def generate_candidates(
    request_data: dict,
    # db: Session = Depends(get_db)  # 注释掉数据库依赖
):
    """
    根据JD分析结果生成候选人列表
    """
    try:
        keywords = request_data.get("keywords", {})
        job_title = request_data.get("jobTitle", "")
        
        # 模拟候选人数据（实际应该从猎聘等平台获取）
        mock_candidates = [
            {
                "id": "1",
                "name": "张三",
                "level": "L1",
                "score": 95.0,
                "swot": {
                    "strengths": ["技术扎实", "经验丰富", "学习能力强"],
                    "weaknesses": ["年龄偏大", "创新性不足"],
                    "opportunities": ["行业发展好", "技术更新快"],
                    "threats": ["竞争激烈", "技术更新快"]
                },
                "summary": "资深前端工程师，有8年开发经验，精通React、Vue等主流框架。",
                "contactInfo": "13800138000"
            },
            {
                "id": "2",
                "name": "李四",
                "level": "L1.5",
                "score": 85.0,
                "swot": {
                    "strengths": ["年轻有活力", "技术栈新", "沟通能力强"],
                    "weaknesses": ["经验相对较少", "稳定性待验证"],
                    "opportunities": ["成长空间大", "适应性强"],
                    "threats": ["经验不足", "稳定性风险"]
                },
                "summary": "年轻有为的前端工程师，有3年开发经验，技术栈新，学习能力强。",
                "contactInfo": "13900139000"
            },
            {
                "id": "3",
                "name": "王五",
                "level": "L2",
                "score": 75.0,
                "swot": {
                    "strengths": ["基础扎实", "工作认真", "团队合作好"],
                    "weaknesses": ["技术深度不够", "创新能力有限"],
                    "opportunities": ["有提升空间", "团队氛围好"],
                    "threats": ["技术发展快", "竞争压力大"]
                },
                "summary": "基础扎实的前端工程师，有5年开发经验，工作认真负责。",
                "contactInfo": "13700137000"
            }
        ]
        
        # 根据关键词过滤候选人（简化处理）
        filtered_candidates = []
        for candidate in mock_candidates:
            # 简单的关键词匹配逻辑
            if any(keyword in candidate["summary"] for keyword in keywords.get("precise", [])):
                filtered_candidates.append(candidate)
        
        # 保存候选人到数据库
        for candidate_data in filtered_candidates:
            # candidate = Candidate(
            #     jd_id=1,  # 这里应该使用实际的JD ID
            #     name=candidate_data["name"],
            #     level=candidate_data["level"],
            #     score=candidate_data["score"],
            #     swot_analysis=candidate_data["swot"],
            #     summary=candidate_data["summary"],
            #     contact_info=candidate_data["contactInfo"]
            # )
            pass  # 临时占位符
        
        # db.commit()
        
        return filtered_candidates
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成候选人失败: {str(e)}")

@app.post("/api/send_message")
async def send_message(
    request_data: dict,
    # db: Session = Depends(get_db)  # 注释掉数据库依赖
):
    """
    发送消息给候选人（触发RPA流程）
    """
    try:
        candidate_id = request_data.get("candidateId")
        jd_info = request_data.get("jdInfo", {})
        
        # 获取候选人信息
        # candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate_id:
            raise HTTPException(status_code=404, detail="候选人不存在")
        
        # 生成话术（简化处理）
        greeting_message = f"""
您好{candidate_id}，我是智讯扬的招聘顾问。

看到您的简历，觉得您非常适合我们正在招聘的{jd_info.get("job_title", "职位")}岗位。

您的{', '.join(jd_info.get("skills", [])[:3])}等技能正是我们需要的。

如果您有兴趣，我们可以进一步沟通，期待您的回复！
        """.strip()
        
        # 保存沟通记录
        # communication_log = CommunicationLog(
        #     candidate_id=candidate_id,
        #     jd_id=1,  # 这里应该使用实际的JD ID
        #     greeting_message=greeting_message,
        #     status="sent",
        #     sent_at=datetime.utcnow()
        # )
        
        # db.add(communication_log)
        
        # 更新候选人状态
        # candidate.rpa_status = "sent"
        # candidate.message_sent_at = datetime.utcnow()
        
        # db.commit()
        
        return {
            "success": True,
            "message": "消息发送成功",
            "greeting_message": greeting_message
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")

@app.get("/api/jds")
async def get_jds(
    # db: Session = Depends(get_db)  # 注释掉数据库依赖
):
    """获取所有JD列表"""
    try:
        # jds = db.query(JD).all()
        return [
            {
                "id": 1,  # 临时ID
                "title": "临时JD",
                "created_at": datetime.now(),
                "diagram_url": ""
            }
        ]
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取JD列表失败: {str(e)}")

@app.get("/api/jds/{jd_id}")
async def get_jd_detail(jd_id: int,
    # db: Session = Depends(get_db)  # 注释掉数据库依赖
):
    """获取JD详情"""
    try:
        # jd = db.query(JD).filter(JD.id == jd_id).first()
        if not jd_id:
            raise HTTPException(status_code=404, detail="JD不存在")
        
        return {
            "id": jd_id,
            "title": "临时JD",
            "content": "临时JD内容",
            "skills": [],
            "products": [],
            "companies": [],
            "keywords": [],
            "mermaid_code": "",
            "diagram_url": "",
            "summary": "",
            "created_at": datetime.now()
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取JD详情失败: {str(e)}")

@app.get("/api/candidates")
async def get_candidates(jd_id: Optional[int] = None,
    # db: Session = Depends(get_db)  # 注释掉数据库依赖
):
    """获取候选人列表"""
    try:
        query = []
        if jd_id:
            query = [
                {
                    "id": 1,  # 临时ID
                    "name": "临时候选人",
                    "level": "L1",
                    "score": 95.0,
                    "swot": {
                        "strengths": ["技术扎实", "经验丰富", "学习能力强"],
                        "weaknesses": ["年龄偏大", "创新性不足"],
                        "opportunities": ["行业发展好", "技术更新快"],
                        "threats": ["竞争激烈", "技术更新快"]
                    },
                    "summary": "临时候选人简介",
                    "contact_info": "13800138000"
                }
            ]
        
        return query
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取候选人列表失败: {str(e)}")

# OSS文件管理相关接口
@app.get("/api/oss/files")
async def get_oss_files(path: str = ""):
    """
    获取OSS指定路径下的文件和文件夹列表
    """
    try:
        print("\n" + "="*20 + " [DIAGNOSTIC LOG] " + "="*20)
        print(f"--- 正在为路径请求文件列表: '{path}' ---")
        
        files = []
        # 使用 delimiter='/' 来模拟文件夹结构
        result = oss_manager.bucket.list_objects(prefix=path, delimiter='/')

        # --- 打印从OSS收到的原始数据 ---
        prefix_list = getattr(result, 'prefix_list', [])
        object_list = getattr(result, 'object_list', [])
        print(f"--- [原始数据] SDK返回的文件夹 (Prefix List): {prefix_list}")
        print(f"--- [原始数据] SDK返回的文件 (Object List): {[o.key for o in object_list]}")
        # --- 日志结束 ---

        # 添加子文件夹
        for p in prefix_list:
            folder_name = p.strip('/').split('/')[-1]
            files.append({
                "name": folder_name,
                "size": 0,
                "lastModified": datetime.now().isoformat(),
                "isDirectory": True,
                "path": p
            })

        # 添加文件
        for obj in object_list:
            if obj.key == path and obj.size == 0:
                continue
            
            file_name = obj.key.split('/')[-1]
            if not file_name: continue # 跳过无效的文件名
            
            files.append({
                "name": file_name,
                "size": obj.size,
                "lastModified": datetime.fromtimestamp(obj.last_modified).isoformat(),
                "isDirectory": False,
                "path": obj.key
            })
        
        print(f"--- [处理结果] 将向前台返回 {len(files)} 个项目 ---")
        print("="*58 + "\n")
        
        return {"files": sorted(files, key=lambda x: (not x['isDirectory'], x['name']))}
    except Exception as e:
        print(f"获取OSS文件列表错误: {e}")
        traceback.print_exc()
        # 保留回退逻辑
        mock_files = [
            {
                "name": "技术部", "size": 0, "lastModified": "2024-01-01T00:00:00Z",
                "isDirectory": True, "path": "技术部/"
            },
            {
                "name": "前端开发工程师.pdf", "size": 1024000, "lastModified": "2024-01-15T10:30:00Z",
                "isDirectory": False, "path": "前端开发工程师.pdf"
            }
        ]
        return {"files": mock_files}

@app.post("/api/oss/create-folder")
async def create_oss_folder(request_data: dict):
    """
    在OSS中创建文件夹
    """
    try:
        path = request_data.get("path", "")
        folder_name = request_data.get("folderName", "")
        
        if not folder_name:
            raise HTTPException(status_code=400, detail="文件夹名称不能为空")
        
        # OSS中创建文件夹实际上就是创建一个以/结尾的空对象
        if path and not path.endswith('/'):
            path += '/'
        folder_path = f"{path}{folder_name}/"
        
        try:
            # 创建一个空对象来表示文件夹
            oss_manager.bucket.put_object(folder_path, "")
            return {
                "success": True,
                "message": "文件夹创建成功",
                "folder_path": folder_path
            }
        except Exception as oss_error:
            print(f"OSS创建文件夹失败: {oss_error}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"OSS创建文件夹失败: {oss_error}")
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"创建文件夹失败: {str(e)}")

@app.delete("/api/oss/delete")
async def delete_oss_files(request_data: dict):
    """
    删除OSS中的文件或文件夹（支持批量删除）
    """
    try:
        paths = request_data.get("paths", [])
        
        if not paths:
            raise HTTPException(status_code=400, detail="文件路径不能为空")
        
        # 支持单个路径的向后兼容
        if isinstance(paths, str):
            paths = [paths]
        elif "path" in request_data:
            paths = [request_data["path"]]
        
        deleted_count = 0
        failed_files = []
        
        for path in paths:
            try:
                # 如果是文件夹，需要删除文件夹内的所有文件
                if path.endswith('/'):
                    # 获取文件夹内的所有对象
                    result = oss_manager.bucket.list_objects(prefix=path)
                    objects_to_delete = [obj.key for obj in getattr(result, 'object_list', [])]
                    
                    # 删除文件夹内的所有文件
                    for obj_key in objects_to_delete:
                        oss_manager.delete_file(obj_key)
                        deleted_count += 1
                    
                    # 删除文件夹标记
                    oss_manager.delete_file(path)
                else:
                    # 删除单个文件
                    oss_manager.delete_file(path)
                    deleted_count += 1
                    
            except Exception as oss_error:
                print(f"删除 {path} 失败: {oss_error}")
                failed_files.append(path)
        
        if failed_files:
            return {
                "success": False,
                "message": f"部分删除失败，成功删除 {deleted_count} 个，失败 {len(failed_files)} 个",
                "failed_files": failed_files
            }
        else:
            return {
                "success": True,
                "message": f"成功删除 {deleted_count} 个项目"
            }
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@app.get("/api/oss/download")
async def download_oss_file(path: str):
    """
    下载OSS中的单个文件
    """
    try:
        if not path:
            raise HTTPException(status_code=400, detail="文件路径不能为空")
        
        # URL解码路径
        import urllib.parse
        decoded_path = urllib.parse.unquote(path)
        print(f"下载文件路径: {decoded_path}")
        
        try:
            # 从OSS获取文件内容
            obj = oss_manager.bucket.get_object(decoded_path)
            content = obj.read()
            
            # 获取文件名，处理中文文件名
            filename = os.path.basename(decoded_path)
            # 对文件名进行URL编码，确保浏览器能正确处理
            encoded_filename = urllib.parse.quote(filename)
            
            return Response(
                content=content,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                    "Content-Length": str(len(content))
                }
            )
        except Exception as oss_error:
            print(f"OSS下载失败: {oss_error}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"OSS下载失败: {oss_error}")
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")

@app.post("/api/oss/download-batch")
async def download_oss_files_batch(request_data: dict):
    """
    批量下载OSS中的文件（打包为zip）
    """
    import zipfile
    import io
    
    try:
        paths = request_data.get("paths", [])
        
        if not paths:
            raise HTTPException(status_code=400, detail="文件路径不能为空")
        
        # 创建内存中的zip文件
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for path in paths:
                try:
                    # 跳过文件夹
                    if path.endswith('/'):
                        continue
                    
                    # URL解码路径
                    import urllib.parse
                    decoded_path = urllib.parse.unquote(path)
                    print(f"批量下载文件路径: {decoded_path}")
                        
                    # 从OSS获取文件内容
                    obj = oss_manager.bucket.get_object(decoded_path)
                    content = obj.read()
                    
                    # 添加到zip文件
                    zip_file.writestr(os.path.basename(decoded_path), content)
                    
                except Exception as file_error:
                    print(f"下载文件 {path} 失败: {file_error}")
                    continue
        
        zip_buffer.seek(0)
        
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=component-library-files.zip"}
        )
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"批量下载失败: {str(e)}")

@app.put("/api/oss/rename")
async def rename_oss_file(request_data: dict):
    """
    重命名OSS中的文件或文件夹
    """
    try:
        old_path = request_data.get("oldPath", "")
        new_name = request_data.get("newName", "")
        
        if not old_path or not new_name:
            raise HTTPException(status_code=400, detail="原路径和新名称不能为空")
        
        # 构建新路径
        path_parts = old_path.split('/')
        path_parts[-1] = new_name if not old_path.endswith('/') else new_name
        new_path = '/'.join(path_parts)
        
        # 如果是文件夹，确保新路径以/结尾
        if old_path.endswith('/') and not new_path.endswith('/'):
            new_path += '/'
        
        try:
            if old_path.endswith('/'):
                # 重命名文件夹：需要重命名文件夹内的所有文件
                result = oss_manager.bucket.list_objects(prefix=old_path)
                objects_to_rename = [obj.key for obj in getattr(result, 'object_list', [])]
                
                for obj_key in objects_to_rename:
                    # 计算新的对象键
                    relative_path = obj_key[len(old_path):]
                    new_obj_key = new_path + relative_path
                    
                    # 复制到新位置
                    oss_manager.bucket.copy_object(oss_manager.bucket.bucket_name, obj_key, new_obj_key)
                    # 删除原文件
                    oss_manager.delete_file(obj_key)
                
                # 重命名文件夹标记
                oss_manager.bucket.copy_object(oss_manager.bucket.bucket_name, old_path, new_path)
                oss_manager.delete_file(old_path)
            else:
                # 重命名单个文件
                oss_manager.bucket.copy_object(oss_manager.bucket.bucket_name, old_path, new_path)
                oss_manager.delete_file(old_path)
            
            return {
                "success": True,
                "message": "重命名成功",
                "new_path": new_path
            }
            
        except Exception as oss_error:
            print(f"OSS重命名失败: {oss_error}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"OSS重命名失败: {oss_error}")
            
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"重命名失败: {str(e)}")

# AI对话相关API端点

@app.get("/api/models")
async def get_available_models():
    """获取可用的AI模型列表"""
    try:
        models = llm_manager.get_available_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@app.post("/api/chat")
async def chat_with_ai(request_data: dict):
    """
    与AI模型对话
    
    Request body:
    {
        "message": "用户消息",
        "model_id": "模型ID (可选，默认glm-4-flash)",
        "system_prompt": "系统提示词 (可选)",
        "conversation_history": [历史对话记录] (可选)
    }
    """
    try:
        message = request_data.get("message", "")
        model_id = request_data.get("model_id", "glm-4-flash")
        system_prompt = request_data.get("system_prompt", "你是一个专业的招聘和人力资源助手，能够帮助用户分析JD、简历，并提供专业的建议。")
        conversation_history = request_data.get("conversation_history", [])
        
        if not message.strip():
            raise HTTPException(status_code=400, detail="消息不能为空")
        
        # 构建消息历史
        messages = []
        
        # 添加系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加对话历史
        for history_item in conversation_history:
            if "role" in history_item and "content" in history_item:
                messages.append({
                    "role": history_item["role"],
                    "content": history_item["content"]
                })
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": message})
        
        # 调用AI模型
        response = await llm_manager.achat(messages, model_id)
        
        return {
            "success": True,
            "response": response,
            "model_used": model_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI对话失败: {str(e)}")

@app.post("/api/chat/simple")
async def simple_chat_with_ai(request_data: dict):
    """
    简单的AI对话接口
    
    Request body:
    {
        "prompt": "用户输入",
        "model_id": "模型ID (可选，默认glm-4-flash)",
        "system_prompt": "系统提示词 (可选)"
    }
    """
    try:
        prompt = request_data.get("prompt", "")
        model_id = request_data.get("model_id", "glm-4-flash")
        system_prompt = request_data.get("system_prompt", "你是一个专业的招聘和人力资源助手。")
        
        if not prompt.strip():
            raise HTTPException(status_code=400, detail="输入不能为空")
        
        # 调用AI模型
        response = await llm_manager.asimple_chat(prompt, system_prompt, model_id)
        
        return {
            "success": True,
            "response": response,
            "model_used": model_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI对话失败: {str(e)}")

# 简历上传相关API端点

@app.post("/api/resume/upload")
async def upload_resume(
    resume_file: UploadFile = File(...),
    path: str = Form("resumes/")
):
    """
    上传简历JSON文件并解析入库
    支持标准格式和猎聘插件格式
    """
    try:
        # 读取JSON文件内容
        content = await resume_file.read()
        json_data = json.loads(content.decode('utf-8'))
        
        print(f"接收到简历数据: {resume_file.filename}")
        
        # 上传文件到OSS
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"{path}{timestamp}_{resume_file.filename}"
        oss_url = oss_manager.upload_bytes(content, object_name)
        
        # 自动识别数据格式并选择相应的映射器
        is_liepin_format = False
        
        # 检查是否为猎聘插件格式
        if isinstance(json_data, list) and len(json_data) > 0:
            first_item = json_data[0]
            if isinstance(first_item, dict):
                # 检查是否包含猎聘插件的特征字段
                liepin_keys = ['0.总体信息', '1.基本信息', '2.求职意向', '3.工作经历', '4.项目经历', '5.教育经历']
                if any(key in first_item for key in liepin_keys):
                    is_liepin_format = True
                    print("检测到猎聘插件格式")
        
        # 根据格式选择映射器
        if is_liepin_format:
            resume, work_experiences, education_experiences, project_experiences = ResumeMapper.map_liepin_json_to_resume(json_data)
        else:
            resume, work_experiences, education_experiences, project_experiences = ResumeMapper.map_json_to_resume(json_data)
        
        # 添加追溯信息
        resume.oss_path = object_name
        resume.oss_url = oss_url
        resume.original_filename = resume_file.filename
        resume.file_format = "liepin_plugin" if is_liepin_format else "standard"
        resume.upload_source = "web_upload"
        
        # 保存到talentdb数据库
        db = next(get_talentdb())
        try:
            # 保存主简历数据
            db.add(resume)
            db.flush()  # 获取resume.id
            
            # 更新关联ID
            for work_exp in work_experiences:
                work_exp.resume_id = resume.id
                db.add(work_exp)
            
            for edu_exp in education_experiences:
                edu_exp.resume_id = resume.id
                db.add(edu_exp)
            
            for proj_exp in project_experiences:
                proj_exp.resume_id = resume.id
                db.add(proj_exp)
            
            db.commit()
            
            return {
                "success": True,
                "message": f"简历上传成功 ({'猎聘插件格式' if is_liepin_format else '标准格式'})",
                "resume_id": resume.id,
                "filename": resume_file.filename,
                "oss_url": oss_url,
                "object_name": object_name,
                "format_type": "liepin_plugin" if is_liepin_format else "standard",
                "work_experiences_count": len(work_experiences),
                "education_experiences_count": len(education_experiences),
                "project_experiences_count": len(project_experiences),
                "trace_info": {
                    "oss_path": object_name,
                    "oss_url": oss_url,
                    "original_filename": resume_file.filename,
                    "file_format": "liepin_plugin" if is_liepin_format else "standard",
                    "upload_source": "web_upload",
                    "upload_time": datetime.now().isoformat()
                }
            }
            
        except Exception as db_error:
            db.rollback()
            print(f"数据库保存失败: {db_error}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"数据库保存失败: {str(db_error)}")
        finally:
            db.close()
            
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON格式错误: {str(e)}")
    except Exception as e:
        print(f"简历上传失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"简历上传失败: {str(e)}")

@app.get("/api/resume/list")
async def list_resumes(
    page: int = 1,
    page_size: int = 10,
    search: str = "",
    sort_order: str = "desc"  # asc 或 desc
):
    """
    获取简历列表
    """
    try:
        db = next(get_talentdb())
        try:
            # 初始化查询，确保即使无搜索关键词时 query 也已定义
            query = db.query(Resume)
            # 搜索功能
            if search:
                search = search.lower()  # 转换为小写以进行不区分大小写的搜索
                query = query.filter(
                    # 基本信息搜索
                    func.lower(Resume.chinese_name).contains(search) |
                    func.lower(Resume.english_name).contains(search) |
                    func.lower(Resume.phone).contains(search) |
                    func.lower(Resume.email).contains(search) |
                    # 职位和技能搜索
                    func.lower(Resume.expected_position).contains(search) |
                    # 使用ANY操作符搜索数组字段
                    func.lower(cast(Resume.skills, String)).contains(search.lower())
                )
            
            # 排序
            if sort_order == "asc":
                query = query.order_by(Resume.created_at.asc())
            else:  # desc
                query = query.order_by(Resume.created_at.desc())
            
            # 分页
            total = query.count()
            resumes = query.offset((page - 1) * page_size).limit(page_size).all()
            
            # 转换为字典
            resume_list = []
            for resume in resumes:
                resume_dict = {
                    "id": resume.id,
                    "resume_number": resume.resume_number,
                    "contact_time_preference": resume.contact_time_preference,
                    "chinese_name": resume.chinese_name,
                    "english_name": resume.english_name,
                    "gender": resume.gender,
                    "current_city": resume.current_city,
                    "phone": resume.phone,
                    "email": resume.email,
                    "summary_total_years": resume.summary_total_years,
                    "expected_position": resume.expected_position,
                    "ai_career_stage": resume.ai_career_stage,
                    "avatar_url": resume.avatar_url,
                    "skills": resume.skills,
                    "languages": resume.languages,
                    "ai_profile": resume.ai_profile,
                    "oss_url": resume.oss_url,
                    "original_filename": resume.original_filename,
                    "file_format": resume.file_format,
                    "upload_source": resume.upload_source,
                    "created_at": resume.created_at.isoformat() if resume.created_at else None
                }
                resume_list.append(resume_dict)
            
            return {
                "success": True,
                "data": resume_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"获取简历列表失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取简历列表失败: {str(e)}")

@app.get("/api/resume/{resume_id}")
async def get_resume_detail(resume_id: int):
    """
    获取简历详情
    """
    try:
        db = next(get_talentdb())
        try:
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if not resume:
                raise HTTPException(status_code=404, detail="简历不存在")
            
            # 获取关联数据
            work_experiences = db.query(WorkExperience).filter(WorkExperience.resume_id == resume_id).all()
            education_experiences = db.query(EducationExperience).filter(EducationExperience.resume_id == resume_id).all()
            project_experiences = db.query(ProjectExperience).filter(ProjectExperience.resume_id == resume_id).all()
            
            # 转换为字典
            resume_dict = {
                "id": resume.id,
                "resume_number": resume.resume_number,
                "contact_time_preference": resume.contact_time_preference,
                "chinese_name": resume.chinese_name,
                "english_name": resume.english_name,
                "gender": resume.gender,
                "birth_date": resume.birth_date.isoformat() if resume.birth_date else None,
                "native_place": resume.native_place,
                "current_city": resume.current_city,
                "political_status": resume.political_status,
                "marital_status": resume.marital_status,
                "health": resume.health,
                "height_cm": resume.height_cm,
                "weight_kg": resume.weight_kg,
                "personality": resume.personality,
                "phone": resume.phone,
                "email": resume.email,
                "wechat": resume.wechat,
                "avatar_url": resume.avatar_url,
                "summary_total_years": resume.summary_total_years,
                "summary_industries": resume.summary_industries,
                "summary_roles": resume.summary_roles,
                "skills": resume.skills,
                "awards": resume.awards,
                "languages": resume.languages,
                "expected_location_range_km": resume.expected_location_range_km,
                "expected_cities": resume.expected_cities,
                "expected_salary_yearly": resume.expected_salary_yearly,
                "expected_salary_monthly": resume.expected_salary_monthly,
                "expected_industries": resume.expected_industries,
                "expected_company_nature": resume.expected_company_nature,
                "expected_company_size": resume.expected_company_size,
                "expected_company_stage": resume.expected_company_stage,
                "expected_position": resume.expected_position,
                "additional_conditions": resume.additional_conditions,
                "job_search_status": resume.job_search_status,
                "ai_profile": resume.ai_profile,
                "ai_swot": resume.ai_swot,
                "ai_career_stage": resume.ai_career_stage,
                "ai_personality": resume.ai_personality,
                "created_at": resume.created_at.isoformat() if resume.created_at else None,
                "work_experiences": [
                    {
                        "id": we.id,
                        "company_name": we.company_name,
                        "company_intro": we.company_intro,
                        "company_size": we.company_size,
                        "company_type": we.company_type,
                        "company_location": we.company_location,
                        "start_date": we.start_date.isoformat() if we.start_date else None,
                        "end_date": we.end_date.isoformat() if we.end_date else None,
                        "position": we.position,
                        "department": we.department,
                        "job_description": we.job_description,
                        "achievements": we.achievements
                    }
                    for we in work_experiences
                ],
                "education_experiences": [
                    {
                        "id": ee.id,
                        "school": ee.school,
                        "major": ee.major,
                        "degree": ee.degree,
                        "start_date": ee.start_date.isoformat() if ee.start_date else None,
                        "end_date": ee.end_date.isoformat() if ee.end_date else None,
                        "main_courses": ee.main_courses,
                        "certificates": ee.certificates,
                        "ranking": ee.ranking
                    }
                    for ee in education_experiences
                ],
                "project_experiences": [
                    {
                        "id": pe.id,
                        "project_name": pe.project_name,
                        "start_date": pe.start_date.isoformat() if pe.start_date else None,
                        "end_date": pe.end_date.isoformat() if pe.end_date else None,
                        "role": pe.role,
                        "project_intro": pe.project_intro,
                        "project_achievements": pe.project_achievements
                    }
                    for pe in project_experiences
                ]
            }
            
            return {
                "success": True,
                "data": resume_dict
            }
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"获取简历详情失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取简历详情失败: {str(e)}")

@app.delete("/api/resume/{resume_id}")
async def delete_resume(resume_id: int):
    """
    删除简历及其关联数据
    """
    try:
        db = next(get_talentdb())
        try:
            # 检查简历是否存在
            resume = db.query(Resume).filter(Resume.id == resume_id).first()
            if not resume:
                raise HTTPException(status_code=404, detail="简历不存在")
            
            # 直接删除简历主记录，数据库会自动级联删除关联记录
            db.delete(resume)
            db.commit()
            
            return {
                "success": True,
                "message": f"简历 {resume.chinese_name or resume.english_name} 已成功删除"
            }
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"删除简历失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"删除简历失败: {str(e)}")

@app.delete("/api/resume/batch")
async def delete_resumes_batch(request: Request):
    """
    批量删除简历 - 改为逐个删除以避免外键约束问题
    """
    try:
        # 从查询参数获取resume_ids
        query_ids = request.query_params.getlist("resume_ids")
        print(f"接收到的查询参数: {query_ids}")
        
        if not query_ids:
            raise HTTPException(status_code=400, detail="请选择要删除的简历")
        
        # 转成 int 列表
        resume_ids = [int(i) for i in query_ids]
        print(f"转换后的简历ID列表: {resume_ids}")

        db = next(get_talentdb())
        try:
            deleted_count = 0
            failed_ids = []
            
            # 逐个删除简历，避免批量删除的外键约束问题
            print(f"开始逐个删除 {len(resume_ids)} 个简历: {resume_ids}")
            for resume_id in resume_ids:
                try:
                    print(f"正在删除简历 ID: {resume_id}")
                    # 检查简历是否存在
                    resume = db.query(Resume).filter(Resume.id == resume_id).first()
                    if not resume:
                        print(f"简历 {resume_id} 不存在")
                        failed_ids.append(resume_id)
                        continue
                    
                    # 删除简历主记录，数据库会自动级联删除关联记录
                    db.delete(resume)
                    deleted_count += 1
                    print(f"简历 {resume_id} 删除成功")
                    
                except Exception as e:
                    print(f"删除简历 {resume_id} 失败: {e}")
                    failed_ids.append(resume_id)
                    db.rollback()
                    # 继续删除下一个简历
            
            # 提交所有成功的删除操作
            if deleted_count > 0:
                db.commit()
            
            if failed_ids:
                return {
                    "success": True,
                    "message": f"成功删除 {deleted_count} 份简历，{len(failed_ids)} 份删除失败",
                    "deleted_count": deleted_count,
                    "failed_ids": failed_ids
                }
            else:
                return {
                    "success": True,
                    "message": f"成功删除 {deleted_count} 份简历",
                    "deleted_count": deleted_count
                }
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        print("PostgreSQL 报错:", e.orig.diag.message_detail)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"批量删除简历失败: {str(e)}")

@app.get("/api/resume/stats")
async def get_resume_stats():
    """
    获取简历统计数据
    """
    try:
        db = next(get_talentdb())
        try:
            # 总人才数量
            total_count = db.query(Resume).count()
            
            # 本月新增人才数量
            current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            new_count = db.query(Resume).filter(Resume.created_at >= current_month_start).count()
            
            # 职位分布（Top 5）
            position_stats = (
                db.query(
                    Resume.expected_position,
                    db.func.count(Resume.id).label('count')
                )
                .filter(Resume.expected_position.isnot(None))
                .group_by(Resume.expected_position)
                .order_by(db.text('count DESC'))
                .limit(5)
                .all()
            )
            
            # 技能分布（Top 10）
            # 使用unnest将数组展开为行
            skill_stats = (
                db.query(
                    db.text('skill'),
                    db.func.count(db.text('skill')).label('count')
                )
                .from_self(
                    db.func.unnest(Resume.skills).label('skill')
                )
                .group_by(db.text('skill'))
                .order_by(db.text('count DESC'))
                .limit(10)
                .all()
            )
            
            # 城市分布（Top 5）
            city_stats = (
                db.query(
                    Resume.current_city,
                    db.func.count(Resume.id).label('count')
                )
                .filter(Resume.current_city.isnot(None))
                .group_by(Resume.current_city)
                .order_by(db.text('count DESC'))
                .limit(5)
                .all()
            )
            
            return {
                "success": True,
                "data": {
                    "total_count": total_count,
                    "new_count": new_count,
                    "position_stats": [
                        {"position": pos, "count": count}
                        for pos, count in position_stats
                    ],
                    "skill_stats": [
                        {"skill": skill, "count": count}
                        for skill, count in skill_stats
                    ],
                    "city_stats": [
                        {"city": city, "count": count}
                        for city, count in city_stats
                    ]
                }
            }
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"获取统计数据失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

@app.get("/api/resume/{resume_id}/positions")
async def get_resume_positions(resume_id: int, db: Session = Depends(get_db)):
    """获取指定简历关联的所有职位"""
    try:
        # 检查简历是否存在（从talentdb检查）
        try:
            talentdb = next(get_talentdb())
            resume = talentdb.query(Resume).filter(Resume.id == resume_id).first()
            if not resume:
                raise HTTPException(status_code=404, detail="简历不存在")
        finally:
            talentdb.close()
        
        # 获取该简历关联的所有职位候选人记录
        position_candidates = db.query(PositionCandidate).filter(
            PositionCandidate.resume_id == resume_id
        ).all()
        
        if not position_candidates:
            return {"success": True, "data": []}
        
        # 获取相关的职位、项目和公司信息
        positions_data = []
        for pc in position_candidates:
            position = db.query(Position).filter(Position.id == pc.position_id).first()
            if not position:
                continue
                
            project = db.query(Project).filter(Project.id == position.project_id).first()
            if not project:
                continue
                
            company = db.query(Company).filter(Company.id == project.company_id).first()
            if not company:
                continue
            
            position_data = {
                "id": position.id,
                "name": position.name,
                "description": position.description,
                "status": position.status,
                "project": {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "status": project.status,
                    "company": {
                        "id": company.id,
                        "name": company.name,
                        "description": company.description
                    }
                },
                "candidate_status": pc.status,
                "candidate_notes": pc.notes,
                "candidate_created_at": pc.created_at,
                "candidate_updated_at": pc.updated_at
            }
            positions_data.append(position_data)
        
        return {"success": True, "data": positions_data}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取简历职位关联失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取简历职位关联失败: {str(e)}")

# 招聘项目管理相关API

@app.get("/api/companies")
async def get_companies(db: Session = Depends(get_db)):
    try:
        print(">>> /api/companies hit")
        companies = db.query(Company).all()
        
        # 构建完整的层级数据结构
        companies_data = []
        for company in companies:
            # 获取公司下的所有项目
            projects = db.query(Project).filter(Project.company_id == company.id).all()
            
            projects_data = []
            for project in projects:
                # 获取项目下的所有职位
                positions = db.query(Position).filter(Position.project_id == project.id).all()
                
                positions_data = []
                for position in positions:
                    # 获取职位下的所有候选人
                    candidates = db.query(PositionCandidate).filter(PositionCandidate.position_id == position.id).all()
                    
                    position_data = {
                        "id": position.id,
                        "name": position.name,
                        "description": position.description,
                        "requirements": position.requirements,
                        "status": position.status,
                        "candidates": [
                            {
                                "id": candidate.id,
                                "status": candidate.status,
                                "notes": candidate.notes,
                                "resume_id": candidate.resume_id
                            } for candidate in candidates
                        ]
                    }
                    positions_data.append(position_data)
                
                project_data = {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "status": project.status,
                    "positions": positions_data
                }
                projects_data.append(project_data)
            
            company_data = {
                "id": company.id,
                "name": company.name,
                "description": company.description,
                "projects": projects_data
            }
            companies_data.append(company_data)
        
        return {"success": True, "data": companies_data}
    except Exception as e:
        if "does not exist" in str(e):
            return {"success": False, "message": "项目管理功能需要数据库管理员手动创建表结构。请联系管理员执行建表脚本。", "data": []}
        else:
            raise HTTPException(status_code=500, detail=f"获取公司列表失败: {str(e)}")

@app.post("/api/companies")
async def create_company(request_data: dict, db: Session = Depends(get_db)):
    try:
        name = request_data.get("name")
        description = request_data.get("description")
        
        if not name:
            raise HTTPException(status_code=400, detail="公司名称不能为空")
            
        company = Company(
            name=name,
            description=description
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        return {"success": True, "data": company}
    except Exception as e:
        if "does not exist" in str(e):
            return {"success": False, "message": "项目管理功能需要数据库管理员手动创建表结构。"}
        else:
            raise HTTPException(status_code=500, detail=f"创建公司失败: {str(e)}")

@app.put("/api/companies/{company_id}")
async def update_company(company_id: int, request_data: dict, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    
    name = request_data.get("name")
    description = request_data.get("description")
    
    if not name:
        raise HTTPException(status_code=400, detail="公司名称不能为空")
    
    company.name = name
    if description is not None:
        company.description = description
    
    db.commit()
    db.refresh(company)
    return {"success": True, "data": company}

@app.delete("/api/companies/{company_id}")
async def delete_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    
    # 级联删除：先删除相关的候选人关联
    db.query(PositionCandidate).filter(
        PositionCandidate.position_id.in_(
            db.query(Position.id).filter(
                Position.project_id.in_(
                    db.query(Project.id).filter(Project.company_id == company_id)
                )
            )
        )
    ).delete(synchronize_session=False)
    
    # 删除相关的职位
    db.query(Position).filter(
        Position.project_id.in_(
            db.query(Project.id).filter(Project.company_id == company_id)
        )
    ).delete(synchronize_session=False)
    
    # 删除相关的项目
    db.query(Project).filter(Project.company_id == company_id).delete(synchronize_session=False)
    
    # 最后删除公司
    db.delete(company)
    db.commit()
    return {"success": True}

@app.get("/api/projects/company/id/{company_id}")
async def get_company_projects(company_id: int, db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.company_id == company_id).all()
    return {"success": True, "data": projects}

@app.post("/api/projects")
async def create_project(request_data: dict, db: Session = Depends(get_db)):
    company_id = request_data.get("company_id")
    name = request_data.get("name")  # 修改为name
    description = request_data.get("description")
    status = request_data.get("status", "active")
    
    if not company_id:
        raise HTTPException(status_code=400, detail="公司ID不能为空")
    if not name:  # 修改为name
        raise HTTPException(status_code=400, detail="项目名称不能为空")
    
    # 检查公司是否存在
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="公司不存在")
    
    project = Project(
        company_id=company_id,
        name=name,  # 修改为name
        description=description,
        status=status
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"success": True, "data": project}

@app.get("/api/projects/{project_id}")
async def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 获取项目的职位信息
    positions = db.query(Position).filter(Position.project_id == project_id).all()
    
    # 获取项目的候选人信息
    candidates = db.query(PositionCandidate).join(Position).filter(Position.project_id == project_id).all()
    
    project_data = {
        "id": project.id,
        "company_id": project.company_id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "positions": positions,
        "candidates": candidates
    }
    
    return {"success": True, "data": project_data}

@app.put("/api/projects/{project_id}")
async def update_project(
    project_id: int,
    request_data: dict,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    name = request_data.get("name")  # 修改为name
    description = request_data.get("description")
    status = request_data.get("status")
    
    if not name:  # 修改为name
        raise HTTPException(status_code=400, detail="项目名称不能为空")
    
    project.name = name  # 修改为name
    if description:
        project.description = description
    if status:
        project.status = status
    
    db.commit()
    db.refresh(project)
    return {"success": True, "data": project}

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    db.delete(project)
    db.commit()
    return {"success": True}

@app.post("/api/projects/{project_id}/position")
async def create_position(
    project_id: int,
    request_data: dict,
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    # 支持前端发送的 title 字段，映射为 name
    name = request_data.get("name") or request_data.get("title")
    description = request_data.get("description")
    requirements = request_data.get("requirements")
    status = request_data.get("status", "active")
    
    if not name:
        raise HTTPException(status_code=400, detail="职位名称不能为空")
    
    position = Position(
        project_id=project_id,
        name=name,
        description=description,
        requirements=requirements,
        status=status
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    return {"success": True, "data": position}

@app.get("/api/projects/{project_id}/positions")
async def get_project_positions(project_id: int, db: Session = Depends(get_db)):
    positions = db.query(Position).filter(Position.project_id == project_id).all()
    return {"success": True, "data": positions}

@app.put("/api/positions/{position_id}")
async def update_position(
    position_id: int,
    request_data: dict,
    db: Session = Depends(get_db)
):
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="职位不存在")
    
    name = request_data.get("name")
    description = request_data.get("description")
    requirements = request_data.get("requirements")
    status = request_data.get("status")
    
    if not name:
        raise HTTPException(status_code=400, detail="职位名称不能为空")
    
    position.name = name
    if description:
        position.description = description
    if requirements:
        position.requirements = requirements
    if status:
        position.status = status
    
    db.commit()
    db.refresh(position)
    return {"success": True, "data": position}

@app.delete("/api/positions/{position_id}")
async def delete_position(position_id: int, db: Session = Depends(get_db)):
    position = db.query(Position).filter(Position.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="职位不存在")
    
    db.delete(position)
    db.commit()
    return {"success": True}

@app.get("/api/positions/{position_id}/candidates")
async def get_position_candidates(position_id: int, db: Session = Depends(get_db)):
    """获取指定职位的候选人列表"""
    try:
        # 检查职位是否存在
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            raise HTTPException(status_code=404, detail="职位不存在")
        
        # 获取职位候选人关联
        position_candidates = db.query(PositionCandidate).filter(
            PositionCandidate.position_id == position_id
        ).all()
        
        # 获取候选人的resume_id列表
        resume_ids = [pc.resume_id for pc in position_candidates]
        
        if not resume_ids:
            return {"success": True, "data": []}
        
        # 从人才库数据库获取详细的简历信息
        try:
            talentdb = next(get_talentdb())
            resumes = talentdb.query(Resume).filter(Resume.id.in_(resume_ids)).all()
            
            # 构造返回数据，包含候选人状态
            candidates_data = []
            for resume in resumes:
                # 找到对应的position_candidate记录
                pc = next((pc for pc in position_candidates if pc.resume_id == resume.id), None)
                candidate_data = {
                    "id": resume.id,
                    "resume_number": resume.resume_number,
                    "chinese_name": resume.chinese_name,
                    "english_name": resume.english_name,
                    "gender": resume.gender,
                    "current_city": resume.current_city,
                    "phone": resume.phone,
                    "email": resume.email,
                    "summary_total_years": resume.summary_total_years,
                    "expected_position": resume.expected_position,
                    "ai_career_stage": resume.ai_career_stage,
                    "skills": resume.skills,
                    "languages": resume.languages,
                    "ai_profile": resume.ai_profile,
                    "created_at": resume.created_at,
                    "oss_url": resume.oss_url,
                    "original_filename": resume.original_filename,
                    "file_format": resume.file_format,
                    "upload_source": resume.upload_source,
                    "avatar_url": resume.avatar_url,
                    # 添加职位候选人状态信息
                    "position_candidate_status": pc.status if pc else "unknown",
                    "position_candidate_notes": pc.notes if pc else "",
                    "position_candidate_created_at": pc.created_at if pc else None
                }
                candidates_data.append(candidate_data)
            
            return {"success": True, "data": candidates_data}
            
        finally:
            talentdb.close()
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取职位候选人失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取职位候选人失败: {str(e)}")

@app.post("/api/positions/{position_id}/candidates/{resume_id}")
async def add_candidate_to_position(
    position_id: int,
    resume_id: int,
    db: Session = Depends(get_db),
    request_data: dict = Body(None)
):
    try:
        # 检查职位是否存在
        position = db.query(Position).filter(Position.id == position_id).first()
        if not position:
            raise HTTPException(status_code=404, detail="职位不存在")
        
        # 检查候选人是否存在（从talentdb检查）
        try:
            talentdb = next(get_talentdb())
            resume = talentdb.query(Resume).filter(Resume.id == resume_id).first()
            if not resume:
                raise HTTPException(status_code=404, detail="候选人不存在")
        except Exception as e:
            print(f"检查候选人失败: {e}")
            raise HTTPException(status_code=500, detail=f"检查候选人失败: {str(e)}")
        finally:
            talentdb.close()
        
        # 检查是否已经存在关联
        existing = db.query(PositionCandidate).filter(
            PositionCandidate.position_id == position_id,
            PositionCandidate.resume_id == resume_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="候选人已经在该职位中")
        
        # 获取请求数据，如果没有则使用默认值
        if request_data is None:
            request_data = {}
        
        status = request_data.get("status", "pending")
        notes = request_data.get("notes", "")
        
        position_candidate = PositionCandidate(
            position_id=position_id,
            resume_id=resume_id,
            status=status,
            notes=notes
        )
        db.add(position_candidate)
        db.commit()
        db.refresh(position_candidate)
        return {"success": True, "data": position_candidate}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"添加候选人到职位失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加候选人到职位失败: {str(e)}")

@app.delete("/api/positions/{position_id}/candidates/{resume_id}")
async def remove_candidate_from_position(
    position_id: int,
    resume_id: int,
    db: Session = Depends(get_db)
):
    position_candidate = db.query(PositionCandidate).filter(
        PositionCandidate.position_id == position_id,
        PositionCandidate.resume_id == resume_id
    ).first()
    if not position_candidate:
        raise HTTPException(status_code=404, detail="候选人不在该职位中")
    
    db.delete(position_candidate)
    db.commit()
    return {"success": True}

@app.patch("/api/positions/{position_id}/candidates/{resume_id}")
async def update_candidate_status(
    position_id: int,
    resume_id: int,
    request_data: dict,
    db: Session = Depends(get_db)
):
    position_candidate = db.query(PositionCandidate).filter(
        PositionCandidate.position_id == position_id,
        PositionCandidate.resume_id == resume_id
    ).first()
    if not position_candidate:
        raise HTTPException(status_code=404, detail="候选人不在该职位中")
    
    status = request_data.get("status")
    notes = request_data.get("notes")
    
    if status:
        position_candidate.status = status
    if notes:
        position_candidate.notes = notes
    
    db.commit()
    db.refresh(position_candidate)
    return {"success": True, "data": position_candidate}

# ==================== 新增: 直接接收JSON的简历上传接口 ====================

# 说明: Chrome 插件端会将解析后的简历以 JSON 形式直接 POST 到此接口。
#       该接口不接收文件，而是从请求体中读取 JSON 数据并写入 PostgreSQL。

@app.post("/api/resume/upload_json")
async def upload_resume_json(
    json_data: Any = Body(..., description="简历 JSON 数据，可为对象或数组"),
    path: str = Query("resumes/", description="OSS 存储路径前缀"),
    save_raw: bool = Query(False, description="是否把原始JSON保存到OSS，默认false")
):
    """
    直接接收简历 JSON 数据并解析入库。

    与 `/api/resume/upload` 功能相同，但省去上传文件这一步，方便浏览器插件直接调用。
    支持标准格式和猎聘插件格式。
    """
    try:
        # 将 JSON 数据序列化为字节流后上传到 OSS，方便后续追溯原始简历
        content_bytes = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"{path}{timestamp}_resume.json"
        oss_url = None
        if save_raw:
            oss_url = oss_manager.upload_bytes(content_bytes, object_name)

        # 判断是否为猎聘插件格式
        is_liepin_format = False
        if isinstance(json_data, list) and json_data:
            first_item = json_data[0]
            if isinstance(first_item, dict):
                liepin_keys = ['0.总体信息', '1.基本信息', '2.求职意向', '3.工作经历', '4.项目经历', '5.教育经历']
                if any(key in first_item for key in liepin_keys):
                    is_liepin_format = True

        # 使用映射器将 JSON 转换为 ORM 对象
        if is_liepin_format:
            resume, work_experiences, education_experiences, project_experiences = ResumeMapper.map_liepin_json_to_resume(json_data)
        else:
            resume, work_experiences, education_experiences, project_experiences = ResumeMapper.map_json_to_resume(json_data)

        # 追溯信息
        resume.oss_path = object_name or ""
        resume.oss_url = oss_url or ""
        resume.original_filename = (object_name.split('/')[-1] if object_name else "uploaded_via_api")
        resume.file_format = "liepin_plugin" if is_liepin_format else "standard"
        resume.upload_source = "browser_plugin"

        # 写入数据库
        db = next(get_talentdb())
        try:
            db.add(resume)
            db.flush()  # 生成 resume.id

            for work_exp in work_experiences:
                work_exp.resume_id = resume.id
                db.add(work_exp)

            for edu_exp in education_experiences:
                edu_exp.resume_id = resume.id
                db.add(edu_exp)

            for proj_exp in project_experiences:
                proj_exp.resume_id = resume.id
                db.add(proj_exp)

            db.commit()

            return {
                "success": True,
                "message": "简历 JSON 上传成功",
                "resume_id": resume.id,
                "oss_url": oss_url,
                "object_name": object_name,
                "format_type": "liepin_plugin" if is_liepin_format else "standard",
                "work_experiences_count": len(work_experiences),
                "education_experiences_count": len(education_experiences),
                "project_experiences_count": len(project_experiences)
            }

        except Exception as db_error:
            db.rollback()
            print(f"数据库保存失败: {db_error}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"数据库保存失败: {str(db_error)}")
        finally:
            db.close()

    except Exception as e:
        print(f"简历 JSON 上传失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"简历 JSON 上传失败: {str(e)}")


@app.post("/api/resume/test_kimi")
async def test_kimi_processing(
    resume_file: UploadFile = File(...),
    path: str = Form("resumes/")
):
    """测试Kimi处理流程的每个步骤"""
    try:
        # 读取文件内容
        file_content = await resume_file.read()
        
        print(f"开始测试Kimi处理流程: {resume_file.filename}")
        
        # 1. 上传文件到Kimi
        file_id = kimi_client.upload_file(file_content, resume_file.filename)
        if not file_id:
            raise HTTPException(status_code=500, detail="上传文件到Kimi失败")
        
        print(f"文件已上传到Kimi，文件ID: {file_id}")
        
        # 2. 运行测试流程
        success = kimi_client.test_file_processing(file_id)
        
        if success:
            return {
                "success": True,
                "message": "Kimi处理流程测试成功",
                "file_id": file_id
            }
        else:
            return {
                "success": False,
                "message": "Kimi处理流程测试失败",
                "file_id": file_id
            }
            
    except Exception as e:
        print(f"Kimi测试失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Kimi测试失败: {str(e)}")


@app.post("/api/resume/upload_with_kimi")
async def upload_resume_with_kimi(
    resume_file: UploadFile = File(...),
    path: str = Form("resumes/"),
    uploaded_by: str = Form("system"),  # 添加上传者参数
    position_id: int = Form(None),  # 添加岗位ID参数
    current_user: User = Depends(get_current_user)  # 获取当前用户
):
    """
    使用Kimi AI标准化简历上传流程
    1. 上传文件到Kimi
    2. 使用Kimi分析并标准化简历
    3. 存储到draft schema等待用户确认
    """
    try:
        # 读取文件内容
        file_content = await resume_file.read()
        
        print(f"开始处理简历文件: {resume_file.filename}")
        
        # 如果提供了岗位ID，获取岗位相关信息
        position_info = None
        if position_id:
            try:
                db = next(get_db())
                position = db.query(Position).filter(Position.id == position_id).first()
                if position:
                    project = db.query(Project).filter(Project.id == position.project_id).first()
                    if project:
                        company = db.query(Company).filter(Company.id == project.company_id).first()
                        if company:
                            position_info = {
                                "position_id": position.id,
                                "position_name": position.name,
                                "project_id": project.id,
                                "project_name": project.name,
                                "company_id": company.id,
                                "company_name": company.name
                            }
                            print(f"获取到岗位信息: {company.name} > {project.name} > {position.name}")
                            db.close()
            except Exception as e:
                print(f"获取岗位信息失败: {e}")
                # 岗位信息获取失败不影响主流程
        
        # 1. 上传文件到Kimi
        print("步骤1: 上传文件到Kimi")
        file_id = kimi_client.upload_file(file_content, resume_file.filename)
        if not file_id:
            raise HTTPException(status_code=500, detail="上传文件到Kimi失败")
        
        print(f"文件已上传到Kimi，文件ID: {file_id}")
        
        # 2. 等待文件处理完成
        print("步骤2: 等待文件处理完成")
        max_retries = 3  # 3次重试
        for i in range(max_retries):
            print(f"第 {i+1} 次检查文件状态...")
            if kimi_client.check_file_status(file_id):
                print(f"文件处理完成，共检查 {i+1} 次")
                break
            if i < max_retries - 1:
                await asyncio.sleep(15)  # 等待15秒后重试
        else:
            print(f"文件处理超时，共检查 {max_retries} 次")
            raise HTTPException(status_code=500, detail="Kimi文件处理超时")
        
        # 3. 使用Kimi标准化简历（带进度反馈）
        print("步骤3: 使用Kimi标准化简历")
        standardized_data = kimi_client.standardize_resume_with_progress(file_id)
        if not standardized_data:
            raise HTTPException(status_code=500, detail="Kimi简历标准化失败")
        
        print(f"简历标准化完成")
        
        # 4. 上传原始文件到OSS
        print("步骤4: 上传原始文件到OSS")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_name = f"{path}{timestamp}_{resume_file.filename}"
        oss_url = oss_manager.upload_bytes(file_content, object_name)
        
        # 5. 将标准化数据存储到draft schema
        print("步骤5: 存储到草稿数据库")
        draft_resume, draft_work_experiences, draft_education_experiences, draft_project_experiences = ResumeMapper.map_json_to_draft_resume(standardized_data)
        
        # 添加追溯信息
        draft_resume.oss_path = object_name
        draft_resume.oss_url = oss_url
        draft_resume.original_filename = resume_file.filename
        draft_resume.file_format = "kimi_standardized"
        draft_resume.upload_source = "web_upload_kimi"
        draft_resume.kimi_file_id = file_id
        draft_resume.draft_status = "pending_review"
        draft_resume.user_id = current_user.id  # 设置用户ID
        
        # 添加岗位关联信息
        if position_info:
            draft_resume.position_id = position_info["position_id"]
            draft_resume.position_name = position_info["position_name"]
            draft_resume.project_id = position_info["project_id"]
            draft_resume.project_name = position_info["project_name"]
            draft_resume.company_id = position_info["company_id"]
            draft_resume.company_name = position_info["company_name"]
        
        # 保存到draft数据库
        db = next(get_draft_db())
        try:
            db.add(draft_resume)
            db.flush()  # 获取draft_resume.id
            
            # 更新关联ID
            for work_exp in draft_work_experiences:
                work_exp.resume_id = draft_resume.id
                db.add(work_exp)
            
            for edu_exp in draft_education_experiences:
                edu_exp.resume_id = draft_resume.id
                db.add(edu_exp)
            
            for proj_exp in draft_project_experiences:
                proj_exp.resume_id = draft_resume.id
                db.add(proj_exp)
            
            db.commit()
            
            return {
                "success": True,
                "message": "简历已通过Kimi标准化并存储到草稿区",
                "draft_resume_id": draft_resume.id,
                "filename": resume_file.filename,
                "oss_url": oss_url,
                "kimi_file_id": file_id,
                "work_experiences_count": len(draft_work_experiences),
                "education_experiences_count": len(draft_education_experiences),
                "project_experiences_count": len(draft_project_experiences),
                "position_info": position_info,
                "next_step": "请前往草稿区查看并确认简历信息"
            }
            
        except Exception as db_error:
            db.rollback()
            print(f"数据库保存失败: {db_error}")
            raise HTTPException(status_code=500, detail=f"数据库保存失败: {str(db_error)}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"Kimi简历上传失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Kimi简历上传失败: {str(e)}")


@app.get("/api/resume/draft/list")
async def list_draft_resumes(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(get_current_user)  # 获取当前用户
):
    """获取草稿简历列表 - 移除状态过滤"""
    try:
        db = next(get_draft_db())
        try:
            # 构建查询 - 只查询当前用户的草稿简历
            query = db.query(DraftResume).filter(DraftResume.user_id == current_user.id)
            
            # 分页
            offset = (page - 1) * page_size
            total = query.count()
            draft_resumes = query.order_by(DraftResume.created_at.desc()).offset(offset).limit(page_size).all()
            
            # 格式化返回数据 - 移除状态相关字段
            draft_list = []
            for draft_resume in draft_resumes:
                draft_dict = {
                    "id": draft_resume.id,
                    "chinese_name": draft_resume.chinese_name,
                    "gender": draft_resume.gender,
                    "current_city": draft_resume.current_city,
                    "phone": draft_resume.phone,
                    "email": draft_resume.email,
                    "expected_position": draft_resume.expected_position,
                    "original_filename": draft_resume.original_filename,
                    "kimi_file_id": draft_resume.kimi_file_id,
                    "created_at": draft_resume.created_at.isoformat() if draft_resume.created_at else None,
                    # 添加岗位关联信息
                    "position_info": {
                        "position_id": draft_resume.position_id,
                        "position_name": draft_resume.position_name,
                        "project_id": draft_resume.project_id,
                        "project_name": draft_resume.project_name,
                        "company_id": draft_resume.company_id,
                        "company_name": draft_resume.company_name
                    } if draft_resume.position_id else None
                }
                draft_list.append(draft_dict)
            
            return {
                "success": True,
                "data": draft_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"获取草稿简历列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取草稿简历列表失败: {str(e)}")


@app.get("/api/resume/draft/{draft_id}")
async def get_draft_resume_detail(
    draft_id: int,
    current_user: User = Depends(get_current_user)  # 获取当前用户
):
    """获取草稿简历详情"""
    try:
        db = next(get_draft_db())
        try:
            draft_resume = db.query(DraftResume).filter(
                DraftResume.id == draft_id,
                DraftResume.user_id == current_user.id
            ).first()
            if not draft_resume:
                raise HTTPException(status_code=404, detail="草稿简历不存在或无权限访问")
            
            # 获取关联数据
            draft_work_experiences = db.query(DraftWorkExperience).filter(DraftWorkExperience.resume_id == draft_id).all()
            draft_education_experiences = db.query(DraftEducationExperience).filter(DraftEducationExperience.resume_id == draft_id).all()
            draft_project_experiences = db.query(DraftProjectExperience).filter(DraftProjectExperience.resume_id == draft_id).all()
            
            # 格式化返回数据
            return {
                "success": True,
                "data": {
                    "basic_info": {
                        "id": draft_resume.id,
                        "resume_number": draft_resume.resume_number,
                        "contact_time_preference": draft_resume.contact_time_preference,
                        "chinese_name": draft_resume.chinese_name,
                        "english_name": draft_resume.english_name,
                        "gender": draft_resume.gender,
                        "birth_date": draft_resume.birth_date.isoformat() if draft_resume.birth_date else None,
                        "native_place": draft_resume.native_place,
                        "current_city": draft_resume.current_city,
                        "political_status": draft_resume.political_status,
                        "marital_status": draft_resume.marital_status,
                        "health": draft_resume.health,
                        "height_cm": draft_resume.height_cm,
                        "weight_kg": draft_resume.weight_kg,
                        "personality": draft_resume.personality,
                        "phone": draft_resume.phone,
                        "email": draft_resume.email,
                        "wechat": draft_resume.wechat,
                        "avatar_url": draft_resume.avatar_url,
                        "kimi_file_id": draft_resume.kimi_file_id
                    },
                    "summary": {
                        "total_years": draft_resume.summary_total_years,
                        "industries": draft_resume.summary_industries,
                        "roles": draft_resume.summary_roles,
                        "skills": draft_resume.skills,
                        "awards": draft_resume.awards,
                        "languages": draft_resume.languages,
                        "highest_education": draft_resume.highest_education
                    },
                    "expectations": {
                        "location_range_km": draft_resume.expected_location_range_km,
                        "cities": draft_resume.expected_cities,
                        "salary_yearly": draft_resume.expected_salary_yearly,
                        "salary_monthly": draft_resume.expected_salary_monthly,
                        "industries": draft_resume.expected_industries,
                        "company_nature": draft_resume.expected_company_nature,
                        "company_size": draft_resume.expected_company_size,
                        "company_stage": draft_resume.expected_company_stage,
                        "position": draft_resume.expected_position,
                        "additional_conditions": draft_resume.additional_conditions,
                        "job_search_status": draft_resume.job_search_status
                    },
                    "ai_analysis": {
                        "profile": draft_resume.ai_profile,
                        "swot": draft_resume.ai_swot,
                        "career_stage": draft_resume.ai_career_stage,
                        "personality": draft_resume.ai_personality
                    },
                    "work_experiences": [
                        {
                            "id": we.id,
                            "company_name": we.company_name,
                            "company_intro": we.company_intro,
                            "company_size": we.company_size,
                            "company_type": we.company_type,
                            "company_stage": we.company_stage,
                            "company_location": we.company_location,
                            "position": we.position,
                            "department": we.department,
                            "start_date": we.start_date.isoformat() if we.start_date else None,
                            "end_date": we.end_date.isoformat() if we.end_date else None,
                            "current_status": we.current_status,
                            "job_description": we.job_description,
                            "job_details": we.job_details,
                            "achievements": we.achievements
                        } for we in draft_work_experiences
                    ],
                    "education_experiences": [
                        {
                            "id": ee.id,
                            "school": ee.school,
                            "major": ee.major,
                            "degree": ee.degree,
                            "start_date": ee.start_date.isoformat() if ee.start_date else None,
                            "end_date": ee.end_date.isoformat() if ee.end_date else None,
                            "main_courses": ee.main_courses,
                            "certificates": ee.certificates,
                            "ranking": ee.ranking
                        } for ee in draft_education_experiences
                    ],
                    "project_experiences": [
                        {
                            "id": pe.id,
                            "project_name": pe.project_name,
                            "role": pe.role,
                            "start_date": pe.start_date.isoformat() if pe.start_date else None,
                            "end_date": pe.end_date.isoformat() if pe.end_date else None,
                            "project_intro": pe.project_intro,
                            "project_achievements": pe.project_achievements
                        } for pe in draft_project_experiences
                    ],
                    # 添加岗位关联信息
                    "position_info": {
                        "position_id": draft_resume.position_id,
                        "position_name": draft_resume.position_name,
                        "project_id": draft_resume.project_id,
                        "project_name": draft_resume.project_name,
                        "company_id": draft_resume.company_id,
                        "company_name": draft_resume.company_name
                    } if draft_resume.position_id else None
                }
            }
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"获取草稿简历详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取草稿简历详情失败: {str(e)}")


@app.post("/api/resume/draft/{draft_id}/confirm")
async def confirm_draft_resume(
    draft_id: int,
    current_user: User = Depends(get_current_user)  # 获取当前用户
):
    """确认草稿简历，将其转移到正式的public schema"""
    try:
        print(f"开始确认草稿简历，draft_id: {draft_id}")
        draft_db = next(get_draft_db())
        talent_db = next(get_talentdb())
        
        try:
            # 获取草稿数据 - 只能确认自己的草稿简历
            draft_resume = draft_db.query(DraftResume).filter(
                DraftResume.id == draft_id,
                DraftResume.user_id == current_user.id
            ).first()
            if not draft_resume:
                raise HTTPException(status_code=404, detail="草稿简历不存在或无权限访问")
            
            print(f"找到草稿简历: {draft_resume.chinese_name}")
            
            # 获取关联数据
            draft_work_experiences = draft_db.query(DraftWorkExperience).filter(DraftWorkExperience.resume_id == draft_id).all()
            draft_education_experiences = draft_db.query(DraftEducationExperience).filter(DraftEducationExperience.resume_id == draft_id).all()
            draft_project_experiences = draft_db.query(DraftProjectExperience).filter(DraftProjectExperience.resume_id == draft_id).all()
            
            print(f"关联数据数量: 工作经历={len(draft_work_experiences)}, 教育经历={len(draft_education_experiences)}, 项目经历={len(draft_project_experiences)}")
            
            # 转换为正式模型
            resume = Resume()
            # 只复制交集字段，避免字段不匹配问题
            intersection_fields = [
                'summary_roles', 'expected_position', 'additional_conditions', 'marital_status',
                'summary_total_years', 'gender', 'email', 'oss_path', 'weight_kg', 'oss_url',
                'ai_profile', 'expected_company_size', 'summary_industries', 'birth_date',
                'native_place', 'upload_source', 'skills', 'expected_company_nature', 'ai_swot',
                'expected_salary_monthly', 'expected_company_stage', 'languages', 'resume_number',
                'highest_education', 'height_cm', 'expected_cities', 'political_status', 'phone',
                'ai_personality', 'expected_industries', 'contact_time_preference', 'health',
                'english_name', 'expected_salary_yearly', 'original_filename', 'job_search_status',
                'avatar_url', 'current_city', 'expected_location_range_km', 'file_format',
                'personality', 'chinese_name', 'awards', 'ai_career_stage', 'wechat'
            ]
            
            for field in intersection_fields:
                if hasattr(draft_resume, field):
                    setattr(resume, field, getattr(draft_resume, field))
            
            # 保存到正式数据库
            talent_db.add(resume)
            talent_db.flush()  # 获取resume.id
            print(f"已创建正式简历，ID: {resume.id}")
            
            # 转换工作经历
            for i, draft_we in enumerate(draft_work_experiences):
                work_exp = WorkExperience()
                work_exp.resume_id = resume.id
                for column in WorkExperience.__table__.columns:
                    if hasattr(draft_we, column.name) and column.name not in ['id', 'resume_id']:
                        setattr(work_exp, column.name, getattr(draft_we, column.name))
                talent_db.add(work_exp)
                print(f"已添加工作经历 {i+1}: {draft_we.company_name}")
            
            # 转换教育经历
            for i, draft_ee in enumerate(draft_education_experiences):
                edu_exp = EducationExperience()
                edu_exp.resume_id = resume.id
                for column in EducationExperience.__table__.columns:
                    if hasattr(draft_ee, column.name) and column.name not in ['id', 'resume_id']:
                        setattr(edu_exp, column.name, getattr(draft_ee, column.name))
                talent_db.add(edu_exp)
                print(f"已添加教育经历 {i+1}: {draft_ee.school}")
            
            # 转换项目经历
            for i, draft_pe in enumerate(draft_project_experiences):
                proj_exp = ProjectExperience()
                proj_exp.resume_id = resume.id
                for column in ProjectExperience.__table__.columns:
                    if hasattr(draft_pe, column.name) and column.name not in ['id', 'resume_id']:
                        setattr(proj_exp, column.name, getattr(draft_pe, column.name))
                talent_db.add(proj_exp)
                print(f"已添加项目经历 {i+1}: {draft_pe.project_name}")
            
            # 提交事务
            print("正式库提交事务...")
            talent_db.commit()
            print("正式库事务提交成功")
            
            # 如果草稿简历有关联的岗位，自动创建岗位候选人关联
            if draft_resume.position_id:
                print(f"草稿简历有关联岗位，开始创建岗位候选人关联...")
                print(f"岗位ID: {draft_resume.position_id}")
                print(f"简历ID: {resume.id}")
                print(f"岗位名称: {draft_resume.position_name}")
                print(f"项目名称: {draft_resume.project_name}")
                print(f"公司名称: {draft_resume.company_name}")
                
                try:
                    # 使用项目管理数据库创建关联
                    project_db = next(get_db())
                    try:
                        # 检查岗位是否存在
                        position = project_db.query(Position).filter(Position.id == draft_resume.position_id).first()
                        if not position:
                            print(f"❌ 岗位不存在: ID={draft_resume.position_id}")
                            return {
                                "success": False,
                                "message": f"岗位不存在: ID={draft_resume.position_id}",
                                "resume_id": resume.id,
                                "draft_id": draft_id
                            }
                        
                        # 检查是否已经存在关联
                        existing = project_db.query(PositionCandidate).filter(
                            PositionCandidate.position_id == draft_resume.position_id,
                            PositionCandidate.resume_id == resume.id
                        ).first()
                        
                        if not existing:
                            # 创建岗位候选人关联
                            position_candidate = PositionCandidate(
                                position_id=draft_resume.position_id,
                                resume_id=resume.id,
                                status="pending",
                                notes=f"从草稿简历自动关联，上传时间: {draft_resume.created_at}"
                            )
                            project_db.add(position_candidate)
                            project_db.commit()
                            print(f"✅ 已成功创建岗位候选人关联: 岗位ID={draft_resume.position_id}, 简历ID={resume.id}")
                            
                            # 验证关联是否创建成功
                            created_association = project_db.query(PositionCandidate).filter(
                                PositionCandidate.position_id == draft_resume.position_id,
                                PositionCandidate.resume_id == resume.id
                            ).first()
                            
                            if created_association:
                                print(f"✅ 验证成功：关联记录已创建，ID={created_association.id}")
                            else:
                                print(f"❌ 验证失败：关联记录未找到")
                        else:
                            print(f"⚠️ 岗位候选人关联已存在: 岗位ID={draft_resume.position_id}, 简历ID={resume.id}")
                    except Exception as e:
                        print(f"❌ 创建岗位候选人关联失败: {e}")
                        print(f"错误类型: {type(e)}")
                        import traceback
                        print(f"错误堆栈: {traceback.format_exc()}")
                        project_db.rollback()
                    finally:
                        project_db.close()
                except Exception as e:
                    print(f"❌ 获取项目管理数据库失败: {e}")
                    print(f"错误类型: {type(e)}")
                    import traceback
                    print(f"错误堆栈: {traceback.format_exc()}")
            else:
                print(f"草稿简历没有关联岗位信息，跳过岗位关联创建")
            
            return {
                "success": True,
                "message": "草稿简历已确认并转移到正式库",
                "resume_id": resume.id,
                "draft_id": draft_id,
                "position_linked": draft_resume.position_id is not None,
                "position_info": {
                    "position_id": draft_resume.position_id,
                    "position_name": draft_resume.position_name,
                    "project_id": draft_resume.project_id,
                    "project_name": draft_resume.project_name,
                    "company_id": draft_resume.company_id,
                    "company_name": draft_resume.company_name
                } if draft_resume.position_id else None
            }
            
        except Exception as e:
            print(f"确认草稿简历过程中发生错误: {e}")
            print(f"错误类型: {type(e)}")
            import traceback
            print(f"错误堆栈: {traceback.format_exc()}")
            talent_db.rollback()
            raise e
        finally:
            draft_db.close()
            talent_db.close()
            
    except Exception as e:
        print(f"确认草稿简历失败: {e}")
        raise HTTPException(status_code=500, detail=f"确认草稿简历失败: {str(e)}")


@app.delete("/api/resume/draft/{draft_id}")
async def delete_draft_resume(draft_id: int):
    """删除草稿简历"""
    try:
        db = next(get_draft_db())
        try:
            draft_resume = db.query(DraftResume).filter(DraftResume.id == draft_id).first()
            if not draft_resume:
                raise HTTPException(status_code=404, detail="草稿简历不存在")
            
            # 删除关联数据（由于外键约束，会自动级联删除）
            db.delete(draft_resume)
            db.commit()
            
            return {
                "success": True,
                "message": "草稿简历已删除"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"删除草稿简历失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除草稿简历失败: {str(e)}")

@app.put("/api/resume/draft/{draft_id}")
async def update_draft_resume(draft_id: int, request_data: dict):
    """更新草稿简历信息"""
    try:
        print(f"接收到更新请求，draft_id: {draft_id}")
        print(f"请求数据: {request_data}")
        
        db = next(get_draft_db())
        try:
            draft_resume = db.query(DraftResume).filter(DraftResume.id == draft_id).first()
            if not draft_resume:
                raise HTTPException(status_code=404, detail="草稿简历不存在")
            
            print(f"找到草稿简历: {draft_resume.chinese_name}")
            print(f"草稿简历字段: {[column.name for column in DraftResume.__table__.columns]}")
            
            # 更新基本信息
            basic_info = request_data.get('basic_info', {})
            for key, value in basic_info.items():
                if hasattr(draft_resume, key):
                    # 特殊处理日期字段
                    if key == 'birth_date' and value:
                        try:
                            from datetime import datetime
                            if isinstance(value, str):
                                draft_resume.birth_date = datetime.strptime(value, '%Y-%m-%d').date()
                            else:
                                setattr(draft_resume, key, value)
                        except:
                            # 如果日期解析失败，跳过这个字段
                            pass
                    else:
                        setattr(draft_resume, key, value)
            
            # 更新联系信息（从basic_info中提取）
            contact_info = request_data.get('contact_info', {})
            for key, value in contact_info.items():
                if hasattr(draft_resume, key):
                    setattr(draft_resume, key, value)
            
            # 同时从basic_info中更新联系信息字段（确保兼容性）
            if 'phone' in basic_info:
                draft_resume.phone = basic_info['phone']
            if 'email' in basic_info:
                draft_resume.email = basic_info['email']
            if 'wechat' in basic_info:
                draft_resume.wechat = basic_info['wechat']
            
            # 更新期望信息
            expectations = request_data.get('expectations', {})
            # 字段映射：前端字段名 -> 数据库字段名
            expectation_mapping = {
                'position': 'expected_position',
                'salary_yearly': 'expected_salary_yearly',
                'salary_monthly': 'expected_salary_monthly',
                'location_range_km': 'expected_location_range_km',
                'cities': 'expected_cities',
                'industries': 'expected_industries',
                'company_nature': 'expected_company_nature',
                'company_size': 'expected_company_size',
                'company_stage': 'expected_company_stage',
                'additional_conditions': 'additional_conditions',
                'job_search_status': 'job_search_status'
            }
            for key, value in expectations.items():
                db_field = expectation_mapping.get(key, key)
                if hasattr(draft_resume, db_field):
                    setattr(draft_resume, db_field, value)
            
            # 更新总结信息
            summary = request_data.get('summary', {})
            print(f"总结信息更新: {summary}")
            # 字段映射：前端字段名 -> 数据库字段名
            summary_mapping = {
                'total_years': 'summary_total_years',
                'industries': 'summary_industries',
                'roles': 'summary_roles',
                'skills': 'skills',
                'awards': 'awards',
                'languages': 'languages',
                'highest_education': 'highest_education'  # 最高学历字段映射
            }
            for key, value in summary.items():
                db_field = summary_mapping.get(key, key)
                print(f"更新字段: {key} -> {db_field} = {value}")
                if hasattr(draft_resume, db_field):
                    setattr(draft_resume, db_field, value)
                    print(f"成功设置字段 {db_field}")
                else:
                    print(f"字段 {db_field} 不存在于模型中")
            
            # 更新AI分析
            ai_analysis = request_data.get('ai_analysis', {})
            # 字段映射：前端字段名 -> 数据库字段名
            ai_mapping = {
                'profile': 'ai_profile',
                'swot': 'ai_swot',
                'career_stage': 'ai_career_stage',
                'personality': 'ai_personality'
            }
            for key, value in ai_analysis.items():
                db_field = ai_mapping.get(key, key)
                if hasattr(draft_resume, db_field):
                    setattr(draft_resume, db_field, value)
            
            # 更新工作经历
            if 'work_experiences' in request_data:
                # 删除现有工作经历
                existing_work = db.query(DraftWorkExperience).filter(DraftWorkExperience.resume_id == draft_id).all()
                for existing in existing_work:
                    db.delete(existing)
                
                # 添加新的工作经历
                for we_data in request_data['work_experiences']:
                    work_exp = DraftWorkExperience()
                    work_exp.resume_id = draft_id
                    for key, value in we_data.items():
                        if hasattr(work_exp, key) and key != 'id':
                            # 特殊处理日期字段
                            if key in ['start_date', 'end_date'] and value:
                                try:
                                    from datetime import datetime
                                    if isinstance(value, str):
                                        setattr(work_exp, key, datetime.strptime(value, '%Y-%m-%d').date())
                                    else:
                                        setattr(work_exp, key, value)
                                except:
                                    # 如果日期解析失败，跳过这个字段
                                    pass
                            else:
                                setattr(work_exp, key, value)
                    db.add(work_exp)
            
            # 更新教育经历
            if 'education_experiences' in request_data:
                # 删除现有教育经历
                existing_education = db.query(DraftEducationExperience).filter(DraftEducationExperience.resume_id == draft_id).all()
                for existing in existing_education:
                    db.delete(existing)
                
                # 添加新的教育经历
                for ee_data in request_data['education_experiences']:
                    edu_exp = DraftEducationExperience()
                    edu_exp.resume_id = draft_id
                    for key, value in ee_data.items():
                        if hasattr(edu_exp, key) and key != 'id':
                            # 特殊处理日期字段
                            if key in ['start_date', 'end_date'] and value:
                                try:
                                    from datetime import datetime
                                    if isinstance(value, str):
                                        setattr(edu_exp, key, datetime.strptime(value, '%Y-%m-%d').date())
                                    else:
                                        setattr(edu_exp, key, value)
                                except:
                                    # 如果日期解析失败，跳过这个字段
                                    pass
                            else:
                                setattr(edu_exp, key, value)
                    db.add(edu_exp)
            
            # 更新项目经历
            if 'project_experiences' in request_data:
                # 删除现有项目经历
                existing_project = db.query(DraftProjectExperience).filter(DraftProjectExperience.resume_id == draft_id).all()
                for existing in existing_project:
                    db.delete(existing)
                
                # 添加新的项目经历
                for pe_data in request_data['project_experiences']:
                    proj_exp = DraftProjectExperience()
                    proj_exp.resume_id = draft_id
                    for key, value in pe_data.items():
                        if hasattr(proj_exp, key) and key != 'id':
                            # 特殊处理日期字段
                            if key in ['start_date', 'end_date'] and value:
                                try:
                                    from datetime import datetime
                                    if isinstance(value, str):
                                        setattr(proj_exp, key, datetime.strptime(value, '%Y-%m-%d').date())
                                    else:
                                        setattr(proj_exp, key, value)
                                except:
                                    # 如果日期解析失败，跳过这个字段
                                    pass
                            else:
                                setattr(proj_exp, key, value)
                    db.add(proj_exp)
            
            # 更新完成
            print("准备提交数据库更改...")
            db.commit()
            print("数据库更改已提交")
            
            return {
                "success": True,
                "message": "草稿简历已更新",
                "draft_id": draft_id
            }
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"更新草稿简历失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新草稿简历失败: {str(e)}")

@app.post("/api/resume/draft/batch/confirm")
async def batch_confirm_draft_resumes(request_data: dict):
    """批量确认草稿简历"""
    try:
        draft_ids = request_data.get('draft_ids', [])
        if not draft_ids:
            raise HTTPException(status_code=400, detail="请选择要确认的草稿简历")
        
        draft_db = next(get_draft_db())
        talent_db = next(get_talentdb())
        
        success_count = 0
        failed_count = 0
        
        try:
            for draft_id in draft_ids:
                try:
                    # 获取草稿数据
                    draft_resume = draft_db.query(DraftResume).filter(DraftResume.id == draft_id).first()
                    if not draft_resume or draft_resume.draft_status != "pending_review":
                        failed_count += 1
                        continue
                    
                    # 获取关联数据
                    draft_work_experiences = draft_db.query(DraftWorkExperience).filter(DraftWorkExperience.resume_id == draft_id).all()
                    draft_education_experiences = draft_db.query(DraftEducationExperience).filter(DraftEducationExperience.resume_id == draft_id).all()
                    draft_project_experiences = draft_db.query(DraftProjectExperience).filter(DraftProjectExperience.resume_id == draft_id).all()
                    
                    # 转换为正式模型
                    resume = Resume()
                    # 只复制交集字段，避免字段不匹配问题
                    intersection_fields = [
                        'summary_roles', 'expected_position', 'additional_conditions', 'marital_status',
                        'summary_total_years', 'gender', 'email', 'oss_path', 'weight_kg', 'oss_url',
                        'ai_profile', 'expected_company_size', 'summary_industries', 'birth_date',
                        'native_place', 'upload_source', 'skills', 'expected_company_nature', 'ai_swot',
                        'expected_salary_monthly', 'expected_company_stage', 'languages', 'resume_number',
                        'highest_education', 'height_cm', 'expected_cities', 'political_status', 'phone',
                        'ai_personality', 'expected_industries', 'contact_time_preference', 'health',
                        'english_name', 'expected_salary_yearly', 'original_filename', 'job_search_status',
                        'avatar_url', 'current_city', 'expected_location_range_km', 'file_format',
                        'personality', 'chinese_name', 'awards', 'ai_career_stage', 'wechat'
                    ]
                    
                    for field in intersection_fields:
                        if hasattr(draft_resume, field):
                            setattr(resume, field, getattr(draft_resume, field))
                    
                    talent_db.add(resume)
                    talent_db.flush()
                    
                    # 转换工作经历
                    for draft_we in draft_work_experiences:
                        work_exp = WorkExperience()
                        work_exp.resume_id = resume.id
                        for column in WorkExperience.__table__.columns:
                            if hasattr(draft_we, column.name) and column.name not in ['id', 'resume_id']:
                                setattr(work_exp, column.name, getattr(draft_we, column.name))
                        talent_db.add(work_exp)
                    
                    # 转换教育经历
                    for draft_ee in draft_education_experiences:
                        edu_exp = EducationExperience()
                        edu_exp.resume_id = resume.id
                        for column in EducationExperience.__table__.columns:
                            if hasattr(draft_ee, column.name) and column.name not in ['id', 'resume_id']:
                                setattr(edu_exp, column.name, getattr(draft_ee, column.name))
                        talent_db.add(edu_exp)
                    
                    # 转换项目经历
                    for draft_pe in draft_project_experiences:
                        proj_exp = ProjectExperience()
                        proj_exp.resume_id = resume.id
                        for column in ProjectExperience.__table__.columns:
                            if hasattr(draft_pe, column.name) and column.name not in ['id', 'resume_id']:
                                setattr(proj_exp, column.name, getattr(draft_pe, column.name))
                        talent_db.add(proj_exp)
                    
                    # 如果草稿简历有关联的岗位，自动创建岗位候选人关联
                    if draft_resume.position_id:
                        print(f"批量确认：草稿简历 {draft_id} 有关联岗位，开始创建岗位候选人关联...")
                        try:
                            # 使用项目管理数据库创建关联
                            project_db = next(get_db())
                            try:
                                # 检查是否已经存在关联
                                existing = project_db.query(PositionCandidate).filter(
                                    PositionCandidate.position_id == draft_resume.position_id,
                                    PositionCandidate.resume_id == resume.id
                                ).first()
                                
                                if not existing:
                                    # 创建岗位候选人关联
                                    position_candidate = PositionCandidate(
                                        position_id=draft_resume.position_id,
                                        resume_id=resume.id,
                                        status="pending",
                                        notes=f"从草稿简历批量确认自动关联，上传时间: {draft_resume.created_at}"
                                    )
                                    project_db.add(position_candidate)
                                    project_db.commit()
                                    print(f"✅ 批量确认：已成功创建岗位候选人关联: 岗位ID={draft_resume.position_id}, 简历ID={resume.id}")
                                else:
                                    print(f"⚠️ 批量确认：岗位候选人关联已存在: 岗位ID={draft_resume.position_id}, 简历ID={resume.id}")
                            except Exception as e:
                                print(f"❌ 批量确认：创建岗位候选人关联失败: {e}")
                                project_db.rollback()
                            finally:
                                project_db.close()
                        except Exception as e:
                            print(f"❌ 批量确认：获取项目管理数据库失败: {e}")
                    
                    # 更新草稿状态
                    draft_resume.draft_status = "approved"
                    draft_resume.review_notes = "批量确认并转移到正式库"
                    
                    success_count += 1
                    
                except Exception as e:
                    print(f"处理草稿简历 {draft_id} 失败: {e}")
                    failed_count += 1
            
            # 提交事务
            talent_db.commit()
            draft_db.commit()
            
            return {
                "success": True,
                "message": f"批量确认完成，成功 {success_count} 个，失败 {failed_count} 个",
                "success_count": success_count,
                "failed_count": failed_count
            }
            
        except Exception as e:
            talent_db.rollback()
            draft_db.rollback()
            raise e
        finally:
            draft_db.close()
            talent_db.close()
            
    except Exception as e:
        print(f"批量确认草稿简历失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量确认草稿简历失败: {str(e)}")


@app.delete("/api/resume/draft/batch")
async def batch_delete_draft_resumes(request_data: dict):
    """批量删除草稿简历"""
    try:
        draft_ids = request_data.get('draft_ids', [])
        if not draft_ids:
            raise HTTPException(status_code=400, detail="请选择要删除的草稿简历")
        
        db = next(get_draft_db())
        try:
            # 批量删除
            result = db.query(DraftResume).filter(DraftResume.id.in_(draft_ids)).delete(synchronize_session=False)
            db.commit()
            
            return {
                "success": True,
                "message": f"成功删除 {result} 个草稿简历",
                "deleted_count": result
            }
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"批量删除草稿简历失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量删除草稿简历失败: {str(e)}")

@app.post("/api/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        print(f"登录请求: username={form_data.username}")
        
        # 查找用户
        user = db.query(User).filter(User.username == form_data.username).first()
        if not user:
            print(f"用户 {form_data.username} 不存在")
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        print(f"找到用户: {user.username}, ID: {user.id}")
        
        # 验证密码
        try:
            if not verify_password(form_data.password, user.password_hash):
                print(f"密码验证失败")
                raise HTTPException(status_code=401, detail="用户名或密码错误")
            print(f"密码验证成功")
        except Exception as e:
            print(f"密码验证异常: {e}")
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 创建访问令牌
        try:
            access_token = create_access_token(data={"sub": user.username})
            print(f"创建访问令牌成功")
        except Exception as e:
            print(f"创建访问令牌失败: {e}")
            raise HTTPException(status_code=500, detail="创建访问令牌失败")
        
        response_data = {
            "access_token": access_token, 
            "token_type": "bearer", 
            "username": user.username
        }
        print(f"登录成功，返回数据: {response_data}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"登录过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")

import redis

# Redis配置（可根据实际情况修改）
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_QUEUE = 'trigger_queue'

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

@app.post("/api/trigger")
async def trigger_task(
    keywords_main: str = Body(..., embed=True, description="主搜索栏关键词，空格分隔"),
    keywords_position: str = Body(..., embed=True, description="职位关键词组，空格分隔"),
    keywords_company: str = Body(..., embed=True, description="公司关键词组，空格分隔"),
    task_id: str = Body(None, embed=True, description="任务ID"),
    company_id: int = Body(None, embed=True, description="公司ID"),
    company_name: str = Body(None, embed=True, description="公司名称"),
    project_id: int = Body(None, embed=True, description="项目ID"),
    project_name: str = Body(None, embed=True, description="项目名称"),
    position_id: int = Body(None, embed=True, description="岗位ID"),
    position_name: str = Body(None, embed=True, description="岗位名称")
):
    """
    接收三组关键词和岗位信息，将任务写入Redis队列
    """
    try:
        task = {
            "main": keywords_main.strip(),
            "position": keywords_position.strip(),
            "company": keywords_company.strip(),
            "timestamp": datetime.now().isoformat()
        }
        if task_id:
            task["task_id"] = task_id
        if company_id is not None:
            task["company_id"] = company_id
        if company_name is not None:
            task["company_name"] = company_name
        if project_id is not None:
            task["project_id"] = project_id
        if project_name is not None:
            task["project_name"] = project_name
        if position_id is not None:
            task["position_id"] = position_id
        if position_name is not None:
            task["position_name"] = position_name
        redis_client.rpush(REDIS_QUEUE, json.dumps(task, ensure_ascii=False))
        return {"success": True, "message": "任务已写入队列", "task": task}
    except Exception as e:
        print(f"写入Redis队列失败: {e}")
        raise HTTPException(status_code=500, detail=f"写入Redis队列失败: {str(e)}")

@app.get("/api/trigger/queue")
async def get_queue_status():
    """查看Redis队列状态和内容，并为每个任务加上岗位信息（如有）"""
    try:
        # 获取队列长度
        queue_length = redis_client.llen(REDIS_QUEUE)
        # 获取队列中的所有任务（不删除）
        tasks = []
        if queue_length > 0:
            # 获取所有任务，但不从队列中移除
            raw_tasks = redis_client.lrange(REDIS_QUEUE, 0, -1)
            for raw_task in raw_tasks:
                try:
                    task = json.loads(raw_task)
                    # 新增：查找岗位信息
                    task_id = task.get("task_id")
                    if task_id:
                        pos_json = redis_client.get(f"position_selection:{task_id}")
                        if pos_json:
                            try:
                                task["position_info"] = json.loads(pos_json)
                            except Exception:
                                task["position_info"] = pos_json
                    tasks.append(task)
                except json.JSONDecodeError:
                    tasks.append({"error": "无法解析任务数据", "aw_task": raw_task})
        return {
            "success": True,
            "queue_name": REDIS_QUEUE,
            "queue_length": queue_length,
            "tasks": tasks
        }
    except Exception as e:
        print(f"读取Redis队列失败: {e}")
        raise HTTPException(status_code=500, detail=f"读取Redis队列失败: {str(e)}")

@app.delete("/api/trigger/queue")
async def clear_queue():
    """清空Redis队列"""
    try:
        deleted_count = redis_client.delete(REDIS_QUEUE)
        return {
            "success": True,
            "message": f"队列已清空，删除了 {deleted_count} 个任务"
        }
    except Exception as e:
        print(f"清空Redis队列失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空Redis队列失败: {str(e)}")

@app.post("/api/generate_task_id")
def generate_task_id():
    """
    生成唯一任务队列ID（UUID），用于岗位选择与分析任务关联。
    """
    task_id = uuid.uuid4().hex
    return {"task_id": task_id}

@app.post("/api/position_selection_cache")
def cache_position_selection(
    task_id: str = Body(..., embed=True, description="任务队列ID"),
    position_info: dict = Body(..., embed=True, description="岗位六字段信息")
):
    """
    接收task_id和岗位六字段，存入Redis，1小时过期。
    """
    try:
        redis_client.set(f"position_selection:{task_id}", json.dumps(position_info, ensure_ascii=False), ex=3600)
        return {"success": True}
    except Exception as e:
        print(f"岗位选择缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"岗位选择缓存失败: {str(e)}")

@app.post("/api/resume/upload_json_with_position")
async def upload_json_with_position(
    task_id: str = Body(..., embed=True, description="任务队列ID"),
    json_data: dict = Body(..., embed=True, description="Puppeteer分析JSON")
):
    """
    接收task_id和Puppeteer发来的JSON，从Redis取岗位信息合并后，入库draft_resume。
    """
    try:
        # 取岗位信息
        pos_json = redis_client.get(f"position_selection:{task_id}")
        if not pos_json:
            raise HTTPException(status_code=400, detail="未找到该任务的岗位信息，请先提交岗位选择")
        position_info = json.loads(pos_json)
        # 合并进json_data
        json_data["position_info"] = position_info
        # 用完即删
        redis_client.delete(f"position_selection:{task_id}")

        # draft_resume入库逻辑（复用标准化JSON入库流程）
        from resume_mapper import ResumeMapper
        draft_resume, draft_work_experiences, draft_education_experiences, draft_project_experiences = ResumeMapper.map_json_to_draft_resume(json_data)
        # 追溯信息可加task_id
        draft_resume.trace_info = {"task_id": task_id, "position_info": position_info}
        db = next(get_draft_db())
        try:
            db.add(draft_resume)
            db.flush()  # 获取draft_resume.id
            for work_exp in draft_work_experiences:
                work_exp.resume_id = draft_resume.id
                db.add(work_exp)
            for edu_exp in draft_education_experiences:
                edu_exp.resume_id = draft_resume.id
                db.add(edu_exp)
            for proj_exp in draft_project_experiences:
                proj_exp.resume_id = draft_resume.id
                db.add(proj_exp)
            db.commit()
            return {
                "success": True,
                "message": "简历JSON+岗位信息已入库草稿区",
                "draft_resume_id": draft_resume.id,
                "position_info": position_info
            }
        except Exception as db_error:
            db.rollback()
            print(f"草稿简历入库失败: {db_error}")
            raise HTTPException(status_code=500, detail=f"草稿简历入库失败: {str(db_error)}")
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        print(f"JSON+岗位信息入库失败: {e}")
        raise HTTPException(status_code=500, detail=f"JSON+岗位信息入库失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 