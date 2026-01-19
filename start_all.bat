@echo off
echo ========================================
echo 中医智能问诊系统 - 一键启动（Docker版）
echo ========================================
echo.

echo [1/6] 启动PostgreSQL数据库容器...
docker-compose up -d

if %errorlevel% neq 0 (
    echo.
    echo 错误: Docker容器启动失败
    echo 请检查Docker是否已安装并运行
    pause
    exit /b 1
)

echo.
echo [2/6] 等待数据库启动...
timeout /t 5 /nobreak >nul

echo.
echo [3/6] 检查数据库连接...
:check_db
docker exec tcm-postgres pg_isready -U postgres >nul 2>&1
if %errorlevel% neq 0 (
    echo 数据库尚未就绪，等待中...
    timeout /t 3 /nobreak >nul
    goto check_db
)
echo 数据库已就绪！

echo.
echo [4/6] 启用pgvector扩展...
docker exec tcm-postgres psql -U postgres -d tcm_agent_db -c "CREATE EXTENSION IF NOT EXISTS vector;" >nul 2>&1

echo.
echo [5/6] 执行数据库迁移...
python manage.py makemigrations
python manage.py migrate

if %errorlevel% neq 0 (
    echo.
    echo 警告: 数据库迁移失败，但继续...
)

echo.
echo [6/6] 插入默认数据...
docker exec tcm-postgres psql -U postgres -d tcm_agent_db -f /docker-entrypoint-initdb.d/insert_default_data.sql 2>nul
if %errorlevel% neq 0 (
    echo 尝试从本地文件插入...
    psql -h localhost -U postgres -d tcm_agent_db -f sql\insert_default_data.sql 2>nul
)

echo.
echo ========================================
echo 系统初始化完成！
echo ========================================
echo.
echo 数据库信息：
echo   - 主机: localhost
echo   - 端口: 5432
echo   - 数据库: tcm_agent_db
echo   - 用户名: postgres
echo   - 密码: postgres123
echo.
echo 启动服务：
echo   1. 后端: python manage.py runserver
echo   2. 前端: cd ui ^&^& npm run dev
echo.
echo 访问地址：
echo   - 前端: http://localhost:3000
echo   - 后端API: http://localhost:8000
echo   - API文档: http://localhost:8000/api/docs/
echo.
echo 按任意键启动后端服务...
pause >nul

python manage.py runserver 0.0.0.0:8000
