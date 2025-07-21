# Vercel部署说明

## 1. 部署前准备

### 1.1 环境变量配置
在Vercel项目设置中添加以下环境变量：

```
# 数据库配置
DB_HOST=your-database-host
DB_PORT=5432
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_NAME=your-database-name

# OSS配置
OSS_ENDPOINT=your-oss-endpoint
OSS_ACCESS_KEY_ID=your-oss-access-key-id
OSS_ACCESS_KEY_SECRET=your-oss-access-key-secret
OSS_BUCKET=your-oss-bucket-name

# API密钥
DEEPSEEK_API_KEY=your-deepseek-api-key
KIMI_API_KEY=your-kimi-api-key

# JWT配置
JWT_SECRET_KEY=your-jwt-secret-key
```

### 1.2 数据库要求
- 确保您的PostgreSQL数据库可以从Vercel的服务器访问
- 数据库需要支持SSL连接
- 建议使用云数据库服务（如Supabase、Railway、Neon等）

## 2. 部署步骤

### 2.1 安装Vercel CLI
```bash
npm install -g vercel
```

### 2.2 登录Vercel
```bash
vercel login
```

### 2.3 部署项目
在Api目录下执行：
```bash
vercel
```

### 2.4 生产环境部署
```bash
vercel --prod
```

## 3. 配置前端

### 3.1 更新API地址
项目已配置为使用正式域名：https://api.zxyang.xin

前端配置已更新：

1. `Web/src/lib/api.ts` 中的 `API_BASE_URL` 已设置为：
```typescript
const API_BASE_URL = "https://api.zxyang.xin/api";
```

2. `Web/vite.config.ts` 中的代理配置已更新为：
```typescript
proxy: {
  '/api': {
    target: 'https://api.zxyang.xin',
    changeOrigin: true,
    secure: true,
    ws: false
  }
}
```

### 3.2 部署前端
将Web目录部署到Vercel或其他静态文件托管服务。

## 4. 常见问题排查

### 4.1 404错误
- 检查 `vercel.json` 配置是否正确
- 确保 `vercel_app.py` 文件存在
- 检查路由配置

### 4.2 数据库连接错误
- 检查环境变量是否正确设置
- 确保数据库允许外部连接
- 检查数据库SSL配置

### 4.3 CORS错误
- 检查前端域名是否在CORS允许列表中
- 确保API响应头正确设置

### 4.4 依赖安装失败
- 检查 `requirements.txt` 文件
- 确保所有依赖都兼容Python 3.11

## 5. 监控和调试

### 5.1 查看日志
在Vercel控制台中查看函数日志：
```bash
vercel logs
```

### 5.2 本地测试
使用Vercel CLI进行本地测试：
```bash
vercel dev
```

## 6. 性能优化

### 6.1 冷启动优化
- 减少不必要的依赖
- 使用连接池管理数据库连接
- 缓存配置信息

### 6.2 内存优化
- 及时释放大对象
- 使用流式处理大文件
- 避免在内存中存储大量数据

## 7. 安全注意事项

### 7.1 环境变量
- 不要在代码中硬编码敏感信息
- 使用Vercel的环境变量功能
- 定期轮换API密钥

### 7.2 CORS配置
- 在生产环境中设置具体的允许域名
- 避免使用 `allow_origins=["*"]`

### 7.3 数据库安全
- 使用强密码
- 限制数据库访问IP
- 启用SSL连接 