@echo off
echo ========================================
echo 中医智能问诊系统 - 前端启动脚本
echo ========================================
echo.

echo [1/3] 检查Node.js环境...
node --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js，请先安装Node.js 18+
    pause
    exit /b 1
)

echo.
echo [2/3] 安装依赖...
cd ui
if not exist "node_modules" (
    call npm install
    if %errorlevel% neq 0 (
        echo 错误: npm install失败
        pause
        exit /b 1
    )
)

echo.
echo [3/3] 启动Vite开发服务器...
echo 访问地址: http://localhost:3000
echo.
npm run dev

pause
