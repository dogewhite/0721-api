# 人才管理系统 API

## 功能模块

### 1. 简历管理
- **简历上传**: 支持PDF、DOCX格式的简历上传
- **简历标准化**: 使用Kimi AI进行简历数据标准化
- **草稿管理**: 暂存待确认的简历数据
- **人才库**: 正式的人才简历库

### 2. 项目管理
- **公司管理**: 管理招聘公司信息
- **项目管理**: 管理招聘项目
- **职位管理**: 管理具体职位信息
- **候选人管理**: 管理职位候选人

### 3. JD分析
- **智能分析**: 使用AI分析职位描述
- **候选人匹配**: 自动匹配合适的候选人
- **分析报告**: 生成详细的分析报告

### 4. OSS文件管理
- **文件上传**: 支持各种格式文件上传
- **文件预览**: 在线预览文件内容
- **文件下载**: 批量下载文件
- **文件夹管理**: 创建和管理文件夹结构

## 数据库结构

### 主要表结构
- `resumes`: 正式人才库简历表
- `draft.draft_resumes`: 草稿简历表
- `companies`: 公司表
- `projects`: 项目表
- `positions`: 职位表
- `position_candidates`: 职位候选人关联表

### 草稿流程
1. 上传简历 → 存储到草稿表
2. 使用Kimi AI标准化数据
3. 人工审核和编辑
4. 确认后转移到正式人才库

## API端点

### 简历管理
- `POST /api/resume/upload_with_kimi`: 上传并标准化简历
- `GET /api/resume/list`: 获取人才库列表
- `GET /api/resume/draft/list`: 获取草稿列表
- `POST /api/resume/draft/{id}/confirm`: 确认草稿简历

### 项目管理
- `GET /api/companies`: 获取公司列表
- `POST /api/companies`: 创建公司
- `GET /api/projects/{id}/positions`: 获取项目职位列表

### JD分析
- `POST /api/upload_jd`: 上传JD文件
- `POST /api/analyze_jd_stream`: 流式分析JD

### OSS管理
- `GET /api/oss/files`: 获取文件列表
- `POST /api/oss/upload`: 上传文件
- `DELETE /api/oss/delete`: 删除文件

## 部署说明

### 环境要求
- Python 3.11+
- PostgreSQL 12+
- Redis (可选，用于缓存)

### 安装步骤
1. 安装依赖: `pip install -r requirements.txt`
2. 配置数据库连接
3. 执行数据库迁移: `psql -f remove_status_fields.sql`
4. 启动服务: `python api.py`

## 注意事项

- 草稿简历确认后会从草稿表删除，转移到正式人才库
- 所有文件操作都通过OSS进行
- AI分析功能需要配置相应的API密钥 