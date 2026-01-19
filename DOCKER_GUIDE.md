# Docker快速启动指南

本指南帮助你使用Docker快速启动中医智能问诊系统。

## 前提条件

1. **安装Docker Desktop**
   - 下载地址：https://www.docker.com/products/docker-desktop
   - 安装后启动Docker Desktop

2. **检查Docker是否运行**
   ```bash
   docker --version
   docker-compose --version
   ```

## 快速启动

### 方式1：一键启动（推荐）

双击运行 `start_all.bat` 脚本，它会自动完成以下步骤：
1. 启动PostgreSQL容器
2. 等待数据库就绪
3. 启用pgvector扩展
4. 执行数据库迁移
5. 插入默认数据
6. 启动Django后端服务

### 方式2：分步启动

#### 步骤1：启动PostgreSQL容器

```bash
docker-compose up -d
```

#### 步骤2：等待数据库启动

```bash
# 检查数据库是否就绪
docker exec tcm-postgres pg_isready -U postgres
```

#### 步骤3：启用pgvector扩展

```bash
docker exec tcm-postgres psql -U postgres -d tcm_agent_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### 步骤4：执行数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 步骤5：插入默认数据

```bash
docker exec tcm-postgres psql -U postgres -d tcm_agent_db -f sql/insert_default_data.sql
```

#### 步骤6：启动后端服务

```bash
python manage.py runserver 0.0.0.0:8000
```

#### 步骤7：启动前端服务（新终端）

```bash
cd ui
npm run dev
```

## 访问地址

启动完成后，访问以下地址：

- **前端界面**：http://localhost:3000
- **后端API**：http://localhost:8000
- **API文档**：http://localhost:8000/api/docs/

## 数据库配置

Docker容器配置的数据库信息：

- **主机**：localhost
- **端口**：5432
- **数据库**：tcm_agent_db
- **用户名**：postgres
- **密码**：postgres123

这些配置已经在 `.env` 文件中设置好，无需修改。

## 常用命令

### 查看容器状态

```bash
docker-compose ps
```

### 查看容器日志

```bash
docker-compose logs -f postgres
```

### 停止容器

```bash
docker-compose down
```

### 停止并删除数据

```bash
docker-compose down -v
```

### 重启容器

```bash
docker-compose restart
```

### 进入PostgreSQL容器

```bash
docker exec -it tcm-postgres psql -U postgres -d tcm_agent_db
```

## 故障排查

### 问题1：Docker未运行

**错误信息**：
```
error during connect: This error may indicate that the docker daemon is not running
```

**解决方案**：
1. 启动Docker Desktop
2. 等待Docker完全启动
3. 重新运行命令

### 问题2：端口5432被占用

**错误信息**：
```
Bind for 0.0.0.0:5432 failed: port is already allocated
```

**解决方案**：
1. 检查是否有其他PostgreSQL实例在运行
2. 修改 `docker-compose.yml` 中的端口映射
3. 或停止其他PostgreSQL实例

### 问题3：数据库连接超时

**错误信息**：
```
connection timeout expired
```

**解决方案**：
1. 等待数据库完全启动（通常需要10-15秒）
2. 检查容器状态：`docker-compose ps`
3. 查看容器日志：`docker-compose logs postgres`

### 问题4：pgvector扩展创建失败

**错误信息**：
```
could not open extension control file
```

**解决方案**：
1. 确保使用的是 `pgvector/pgvector:pg16` 镜像
2. 重新创建容器：
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

## 数据备份

### 备份数据库

```bash
docker exec tcm-postgres pg_dump -U postgres tcm_agent_db > backup.sql
```

### 恢复数据库

```bash
docker exec -i tcm-postgres psql -U postgres tcm_agent_db < backup.sql
```

## 清理

### 清理所有容器和数据

```bash
docker-compose down -v
docker system prune -a
```

## 注意事项

1. **数据持久化**：数据存储在Docker卷中，停止容器不会丢失数据
2. **端口冲突**：确保5432端口未被占用
3. **资源占用**：PostgreSQL容器需要至少512MB内存
4. **生产环境**：生产环境建议修改默认密码

## 下一步

启动成功后，你可以：

1. 访问前端界面：http://localhost:3000
2. 创建知识库并上传文档
3. 创建应用并配置工作流
4. 进行智能问诊对话

详细功能说明请参考 [README.md](README.md)
