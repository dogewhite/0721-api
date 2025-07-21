# Vercel部署脚本
Write-Host "🚀 开始部署到Vercel..." -ForegroundColor Green

# 检查是否安装了Vercel CLI
try {
    $vercelVersion = vercel --version
    Write-Host "✅ Vercel CLI已安装: $vercelVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Vercel CLI未安装，正在安装..." -ForegroundColor Red
    npm install -g vercel
}

# 检查是否已登录
try {
    vercel whoami
    Write-Host "✅ 已登录Vercel" -ForegroundColor Green
} catch {
    Write-Host "❌ 未登录Vercel，请先登录..." -ForegroundColor Red
    vercel login
    exit 1
}

# 检查必要文件
$requiredFiles = @("vercel.json", "vercel_app.py", "requirements.txt")
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ 找到文件: $file" -ForegroundColor Green
    } else {
        Write-Host "❌ 缺少文件: $file" -ForegroundColor Red
        exit 1
    }
}

# 部署到Vercel
Write-Host "📦 正在部署..." -ForegroundColor Yellow
vercel --prod

Write-Host "🎉 部署完成！" -ForegroundColor Green
Write-Host "📝 请检查Vercel控制台获取部署URL" -ForegroundColor Cyan
Write-Host "🔧 记得在Vercel项目设置中配置环境变量" -ForegroundColor Cyan 