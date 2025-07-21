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
        # 这里添加DeepSeek API密钥，用户需要替换为实际的API密钥
        return "sk-a0e0517e24b648ad8456b81906f1fd9d"  # 请替换为实际的DeepSeek API密钥
    
    def get_kimi_api_key(self) -> str:
        """获取Kimi API密钥"""
        return self.config.get('kimi_api_key', '')
    
    def get_database_url(self):
        """获取数据库连接URL（兼容旧代码）"""
        return self.get_db_url()
    
    def get_oss_config_dict(self):
        """获取OSS配置字典"""
        return {
            'endpoint': self.config.get('OSS_ENDPOINT', ''),
            'access_key_id': self.config.get('OSS_ACCESS_KEY_ID', ''),
            'access_key_secret': self.config.get('OSS_ACCESS_KEY_SECRET', ''),
            'bucket': self.config.get('OSS_BUCKET', ''),
            'bucket_name': self.config.get('OSS_BUCKET_NAME', self.config.get('OSS_BUCKET', ''))
        }

    def get_db_url(self):
        """获取数据库URL"""
        return f"postgresql://{self.config.get('DB_USER')}:{self.config.get('DB_PASSWORD')}@{self.config.get('DB_HOST')}:{self.config.get('DB_PORT')}/{self.config.get('DB_NAME')}"

    def get_talentdb_url(self):
        """获取人才库数据库URL，兼容draft_models等调用"""
        return self.get_db_url()

# 全局配置实例
config_loader = ConfigLoader() 