# DeepSeek API 配置指南

## 🎯 概述

本项目现已支持DeepSeek API，包括DeepSeek-V3和DeepSeek-R1两个模型。用户可以在AI对话模块中选择不同的模型进行对话。

## 🔑 获取DeepSeek API密钥

1. **访问DeepSeek官网**
   - 访问 [https://platform.deepseek.com](https://platform.deepseek.com)
   - 注册账号并登录

2. **申请API密钥**
   - 进入API控制台
   - 创建新的API密钥
   - 复制生成的API密钥（格式通常为：`sk-xxxxxxxxxxxxxxxxxx`）

## ⚙️ 配置API密钥

### 方法1：修改配置文件（推荐）

编辑 `Api/config_loader.py` 文件：

```python
def get_deepseek_api_key(self) -> str:
    """获取DeepSeek API密钥"""
    # 将下面的密钥替换为你的实际API密钥
    return "sk-your-actual-deepseek-api-key-here"
```

### 方法2：环境变量（可选）

你也可以通过环境变量设置：

```bash
export DEEPSEEK_API_KEY="sk-your-actual-deepseek-api-key-here"
```

然后修改 `config_loader.py`：

```python
import os

def get_deepseek_api_key(self) -> str:
    """获取DeepSeek API密钥"""
    return os.getenv("DEEPSEEK_API_KEY", "sk-your-deepseek-api-key-here")
```

## 🚀 支持的模型

### 1. DeepSeek-V3 (`deepseek-chat`)
- **特点**: 通用对话模型，平衡了性能和效率
- **适用场景**: 日常对话、文档分析、代码解释等
- **优势**: 响应速度快，成本较低

### 2. DeepSeek-R1 (`deepseek-reasoner`)  
- **特点**: 推理增强模型，具备强大的逻辑推理能力
- **适用场景**: 复杂问题分析、逻辑推理、策略制定等
- **优势**: 推理能力强，适合复杂任务

## 🧪 测试配置

配置完成后，可以运行测试脚本验证：

### 测试DeepSeek客户端
```bash
cd Api
python test_deepseek.py
```

### 测试LLM管理器
```bash
cd Api
python test_llm_manager.py
```

### 启动Web服务
```bash
cd Api
python run_server.py
```

## 💡 使用说明

1. **启动服务**：运行后端API服务
2. **打开前端**：访问 `Web/index.html`
3. **选择模型**：在右侧AI助手面板的模型选择器中选择所需模型
4. **开始对话**：在输入框中输入问题，AI会根据选择的模型回复

## ⚠️ 注意事项

1. **API配额**：DeepSeek API有使用配额限制，请合理使用
2. **网络要求**：需要稳定的网络连接访问DeepSeek API
3. **模型选择**：
   - 普通对话推荐使用 DeepSeek-V3
   - 复杂推理任务推荐使用 DeepSeek-R1
4. **成本控制**：DeepSeek-R1的成本相对较高，请根据需要选择

## 🔧 故障排除

### 常见问题

1. **API密钥无效**
   - 检查密钥格式是否正确
   - 确认密钥是否已激活
   - 检查账户余额

2. **网络连接失败**
   - 检查网络连接
   - 确认防火墙设置
   - 尝试使用代理

3. **模型不可用**
   - 检查API密钥权限
   - 确认选择的模型是否支持

### 调试方法

1. 查看后端日志输出
2. 使用浏览器开发者工具查看网络请求
3. 运行测试脚本排查问题

## 📞 技术支持

如遇问题，请：
1. 查看控制台错误信息
2. 运行测试脚本诊断
3. 检查API官方文档：[DeepSeek API文档](https://platform.deepseek.com/api-docs/) 