@echo off
echo ========================================
echo 中医智能问诊系统 - 快速启动
echo ========================================
echo.

echo [1/4] 启动Django开发服务器...
echo 注意：此脚本跳过数据库迁移，仅用于开发测试
echo.
python manage.py runserver 0.0.0.0:8000

if %errorlevel% neq 0 (
    echo.
    echo 错误: Django服务器启动失败
    echo 请检查：
    echo   1. Python是否已安装
    echo   2. .env文件配置是否正确
    echo   3. 端口8000是否被占用
    pause
    exit /b 1
)

echo.
echo Django服务器已启动！
echo 访问地址: http://localhost:8000
echo API文档: http://localhost:8000/api/docs/
echo.
echo 按Ctrl+C停止服务器
pause
