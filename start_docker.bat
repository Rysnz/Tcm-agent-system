@echo off
echo ========================================
echo 中医智能问诊系统 - Docker启动
echo ========================================
echo.

echo [1/4] 启动PostgreSQL数据库容器...
docker-compose up -d

if %errorlevel% neq 0 (
    echo.
    echo 错误: Docker容器启动失败
    echo 请检查：
    echo   1. Docker是否已安装并运行
    echo   2. 端口5432是否被占用
    pause
    exit /b 1
)

echo.
echo [2/4] 等待数据库启动...
timeout /t 5 /nobreak >nul

echo.
echo [3/4] 检查数据库连接...
docker exec tcm-postgres pg_isready -U postgres

if %errorlevel% neq 0 (
    echo.
    echo 警告: 数据库尚未就绪，继续尝试...
    timeout /t 5 /nobreak >nul
)

echo.
echo [4/4] 启用pgvector扩展...
docker exec tcm-postgres psql -U postgres -d tcm_agent_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

if %errorlevel% neq 0 (
    echo.
    echo 警告: pgvector扩展创建失败，但继续...
)

echo.
echo ========================================
echo PostgreSQL数据库已启动！
echo ========================================
echo.
echo 数据库信息：
echo   - 主机: localhost
echo   - 端口: 5432
echo   - 数据库: tcm_agent_db
echo   - 用户名: postgres
echo   - 密码: postgres123
echo.
echo 下一步：
echo   1. 执行数据库迁移: python manage.py migrate
echo   2. 插入默认数据: psql -h localhost -U postgres -d tcm_agent_db -f sql\insert_default_data.sql
echo   3. 启动后端: python manage.py runserver
echo   4. 启动前端: cd ui ^&^& npm run dev
echo.
pause
