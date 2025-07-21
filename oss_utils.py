import oss2
import os
from datetime import datetime
from config_loader import config_loader
import traceback

class OSSManager:
    def __init__(self):
        oss_config = config_loader.get_oss_config_dict()
        # 兼容旧配置文件（OSS_BUCKET）和新字段（OSS_BUCKET_NAME）
        self.bucket_name = oss_config.get('bucket') or oss_config.get('bucket_name')
        self.auth = oss2.Auth(oss_config['access_key_id'], oss_config['access_key_secret'])
        self.bucket = oss2.Bucket(self.auth, oss_config['endpoint'], self.bucket_name)
        # 移除 endpoint 中的协议头，用于URL拼接
        self.endpoint_for_url = self.bucket.endpoint.replace('https://', '').replace('http://', '')
    
    def upload_file(self, file_path, object_name=None):
        """上传文件到OSS"""
        try:
            if object_name is None:
                # 生成默认对象名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_ext = os.path.splitext(file_path)[1]
                object_name = f"uploads/{timestamp}{file_ext}"
            
            # 上传文件
            result = self.bucket.put_object_from_file(object_name, file_path)
            
            if result.status == 200:
                # 返回文件URL
                return f"https://{self.bucket.bucket_name}.{self.endpoint_for_url}/{object_name}"
            else:
                raise Exception(f"上传失败，状态码: {result.status}")
                
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"OSS上传错误: {e}")
    
    def upload_bytes(self, data, object_name):
        """上传字节数据到OSS"""
        try:
            result = self.bucket.put_object(object_name, data)
            
            if result.status == 200:
                return f"https://{self.bucket.bucket_name}.{self.endpoint_for_url}/{object_name}"
            else:
                raise Exception(f"上传失败，状态码: {result.status}")
                
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"OSS上传错误: {e}")
    
    def download_file(self, object_name, local_path):
        """从OSS下载文件"""
        try:
            self.bucket.get_object_to_file(object_name, local_path)
            return True
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"OSS下载错误: {e}")
    
    def delete_file(self, object_name):
        """删除OSS文件"""
        try:
            self.bucket.delete_object(object_name)
            return True
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"OSS删除错误: {e}")
    
    def file_exists(self, object_name):
        """检查文件是否存在"""
        try:
            return self.bucket.object_exists(object_name)
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"OSS检查文件存在性错误: {e}")
    
    def get_file_url(self, object_name, expires=3600):
        """获取文件临时访问URL"""
        try:
            url = self.bucket.sign_url('GET', object_name, expires)
            return url
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"OSS获取URL错误: {e}")

def download_file_from_oss(object_name):
    """从OSS下载文件并返回内容"""
    try:
        result = oss_manager.bucket.get_object(object_name)
        return result.read()
    except Exception as e:
        print(f"OSS下载文件错误: {e}")
        traceback.print_exc()
        return None

# 全局OSS管理器实例
oss_manager = OSSManager() 