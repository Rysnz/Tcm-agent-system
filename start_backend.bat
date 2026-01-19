@echo off
echo ========================================
echo 中医智能问诊系统 - 启动脚本
echo ========================================
echo.

echo [1/5] 检查Python环境...
python --version
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.11+
    pause
    exit /b 1
)

echo.
echo [2/5] 检查PostgreSQL连接...
echo 注意: 请确保PostgreSQL已安装并运行
echo.

echo [3/5] 初始化数据库...
python manage.py makemigrations
if %errorlevel% neq 0 (
    echo 警告: makemigrations失败，但继续...
)

python manage.py migrate
if %errorlevel% neq 0 (
    echo 错误: 数据库迁移失败
    pause
    exit /b 1
)

echo.
echo [4/5] 启动Django开发服务器...
echo 访问地址: http://localhost:8000
echo API文档: http://localhost:8000/api/docs/
echo.
python manage.py runserver

pause
