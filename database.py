from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config_loader import config_loader

# 创建数据库引擎
def create_database_if_not_exists():
    # 连接到默认的postgres数据库
    default_engine = create_engine(
        f"postgresql://{config_loader.config.get('DB_USER')}:{config_loader.config.get('DB_PASSWORD')}@{config_loader.config.get('DB_HOST')}:{config_loader.config.get('DB_PORT')}/postgres"
    )
    
    # 检查目标数据库是否存在
    with default_engine.connect() as conn:
        # 设置自动提交
        conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # 检查数据库是否存在
        result = conn.execute(text(
            f"SELECT 1 FROM pg_database WHERE datname = '{config_loader.config.get('DB_NAME')}'"
        ))
        exists = result.scalar()
        
        if not exists:
            # 创建数据库
            conn.execute(text(
                f"CREATE DATABASE {config_loader.config.get('DB_NAME')}"
            ))
            print(f"数据库 {config_loader.config.get('DB_NAME')} 已创建")

# 创建数据库引擎
engine = create_engine(config_loader.get_db_url())

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 初始化数据库
def init_db():
    try:
        create_database_if_not_exists()
    except Exception:
        pass
    
    # 导入models.py中的Base，确保使用同一个Base实例
    from models import Base
    
    # 创建所有表（包括新的项目管理表）
    Base.metadata.create_all(bind=engine)
    
    # 若权限不足创建schema会失败，这里忽略该错误
    try:
        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text("SELECT 1"))
    except Exception:
        pass

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 