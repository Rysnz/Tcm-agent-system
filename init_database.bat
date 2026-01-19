@echo off
echo ========================================
echo 中医智能问诊系统 - 数据库初始化
echo ========================================
echo.

echo [1/3] 检查PostgreSQL连接...
echo 注意：请确保PostgreSQL已安装并运行
echo.

echo [2/3] 执行数据库迁移...
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
echo [3/3] 插入默认数据...
psql -h localhost -U postgres -d tcm_agent_db -f sql\insert_default_data.sql
if %errorlevel% neq 0 (
    echo 错误: 插入默认数据失败
    echo 请检查：
    echo   1. PostgreSQL是否运行
    echo   2. 数据库名称是否正确（tcm_agent_db）
    echo   3. 用户名密码是否正确
    pause
    exit /b 1
)

echo.
echo ========================================
echo 初始化完成！
echo ========================================
echo.
echo 下一步：
echo   1. 启动后端服务: python manage.py runserver
echo   2. 启动前端服务: cd ui ^&^& npm run dev
echo   3. 访问系统: http://localhost:3000
echo.
pause
