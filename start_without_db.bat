@echo off
echo ========================================
echo 中医智能问诊系统 - 快速启动（跳过数据库迁移）
echo ========================================
echo.

echo 注意：此脚本跳过数据库迁移，仅用于快速测试
echo 如果需要完整功能，请先配置PostgreSQL数据库
echo.

echo [1/2] 启动Django开发服务器...
echo 访问地址: http://localhost:8000
echo API文档: http://localhost:8000/api/docs/
echo.
python manage.py runserver 0.0.0.0:8000

if %errorlevel% neq 0 (
    echo.
    echo 错误: Django服务器启动失败
    echo 请检查：
    echo   1. Python是否已安装
    echo   2. 端口8000是否被占用
    pause
    exit /b 1
)

pause
