import os
import configparser
from pathlib import Path

class ConfigLoader:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.oss_config_path = self.base_path / "Oss_config.txt"
        self.sql_config_path = self.base_path / "SQL_config.txt"
        self.config = {}
        self.load_config()
        
    def get_env_or_config(self, key: str, default: str = "") -> str:
        """优先从环境变量获取配置，如果没有则从配置文件获取"""
        return os.environ.get(key, self.config.get(key, default))
        
    def load_config(self):
        """读取配置文件"""
        try:
            # 读取OSS配置
            with open(self.oss_config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    if line and '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key.strip()] = value.strip().strip("'")
            
            # 读取SQL配置
            with open(self.sql_config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line and '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key.strip()] = value.strip()
                    elif line == 'address:':
                        if i + 1 < len(lines):
                            self.config['DB_HOST'] = lines[i + 1].strip()
                    elif line == 'port:':
                        if i + 1 < len(lines):
                            self.config['DB_PORT'] = lines[i + 1].strip()
                    elif line == 'account:':
                        if i + 1 < len(lines):
                            self.config['DB_USER'] = lines[i + 1].strip()
                    elif line == 'password:':
                        if i + 1 < len(lines):
                            self.config['DB_PASSWORD'] = lines[i + 1].strip()
                    elif line == 'database:':
                        if i + 1 < len(lines):
                            self.config['DB_NAME'] = lines[i + 1].strip()
            
            return self.config
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {self.oss_config_path} 或 {self.sql_config_path}")
        except Exception as e:
            raise Exception(f"读取配置失败: {e}")
    
    def get_deepseek_api_key(self) -> str:
        """获取DeepSeek API密钥"""
        return self.get_env_or_config("DEEPSEEK_API_KEY", "sk-a0e0517e24b648ad8456b81906f1fd9d")
    
    def get_kimi_api_key(self) -> str:
        """获取Kimi API密钥"""
        return self.get_env_or_config('KIMI_API_KEY', '')
    
    def get_database_url(self):
        """获取数据库连接URL（兼容旧代码）"""
        return self.get_db_url()
    
    def get_oss_config_dict(self):
        """获取OSS配置字典"""
        return {
            'endpoint': self.get_env_or_config('OSS_ENDPOINT', ''),
            'access_key_id': self.get_env_or_config('OSS_ACCESS_KEY_ID', ''),
            'access_key_secret': self.get_env_or_config('OSS_ACCESS_KEY_SECRET', ''),
            'bucket': self.get_env_or_config('OSS_BUCKET', ''),
            'bucket_name': self.get_env_or_config('OSS_BUCKET_NAME', self.get_env_or_config('OSS_BUCKET', ''))
        }

    def get_db_url(self):
        """获取数据库URL"""
        return f"postgresql://{self.get_env_or_config('DB_USER')}:{self.get_env_or_config('DB_PASSWORD')}@{self.get_env_or_config('DB_HOST')}:{self.get_env_or_config('DB_PORT')}/{self.get_env_or_config('DB_NAME')}"

    def get_talentdb_url(self):
        """获取人才库数据库URL，兼容draft_models等调用"""
        return self.get_db_url()

# 全局配置实例
config_loader = ConfigLoader() 