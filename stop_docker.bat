@echo off
echo ========================================
echo 中医智能问诊系统 - 停止服务
echo ========================================
echo.

echo [1/2] 停止Docker容器...
docker-compose down

echo.
echo [2/2] 清理提示...
echo.
echo Docker容器已停止
echo 数据卷已保留，数据不会丢失
echo.
echo 如需完全删除数据，请运行:
echo   docker-compose down -v
echo.
pause
