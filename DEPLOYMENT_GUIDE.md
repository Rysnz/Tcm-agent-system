# TCM Agent System 部署指南

## 部署方案选择

### 方案一：传统服务器部署（推荐）

#### 1.1 准备工作
```bash
# 安装系统依赖
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib libpq-dev

# 克隆项目
git clone <your-repo-url> tcm-agent-system
cd tcm-agent-system

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 安装PostgreSQL扩展
sudo -u postgres psql -c "CREATE EXTENSION vector;"
```

#### 1.2 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件
nano .env
```

需要配置的环境变量：
```env
# 数据库配置
POSTGRES_DB=tcm_agent_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Django配置
DJANGO_SETTINGS_MODULE=apps.tcm.settings
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=False

# Hugging Face配置（可选）
HF_ENDPOINT=https://hf-mirror.com

# 模型API配置
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.xiaomimimo.com/v1/chat/completions
```

#### 1.3 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 1.4 收集静态文件
```bash
python manage.py collectstatic --noinput
```

#### 1.5 配置Gunicorn
创建 `/etc/systemd/system/tcm-agent.service`:

```ini
[Unit]
Description=TCM Agent System Django Application
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/tcm-agent-system
Environment="PATH=/path/to/tcm-agent-system/venv/bin"
ExecStart=/path/to/tcm-agent-system/venv/bin/gunicorn \
    apps.tcm.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile /var/log/tcm-agent/access.log \
    --error-logfile /var/log/tcm-agent/error.log

[Install]
WantedBy=multi-user.target

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable tcm-agent
sudo systemctl start tcm-agent
```

#### 1.6 配置Nginx
创建 `/etc/nginx/sites-available/tcm-agent`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $scheme;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/tcm-agent-system/static;
        expires 30d;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/tcm-agent /etc/nginx/sites-enabled/
sudo nginx -t
```

---

### 方案二：PaaS平台部署

#### 2.1 Render（推荐）

1. 在 [https://render.com](https://render.com) 注册账号
2. 创建新Web Service
   - 选择"Python"
   - 连接GitHub仓库
   - 构建命令：`pip install -r requirements.txt && python manage.py collectstatic`
   - 启动命令：`gunicorn apps.tcm.wsgi:application --bind 0.0.0.0:8000`
3. 添加PostgreSQL数据库
   - 在Render控制台添加PostgreSQL实例
   - 配置环境变量（见方案一的环境变量列表）
4. 部署

#### 2.2 Railway

1. 在 [https://railway.app](https://railway.app) 注册账号
2. 创建新项目
3. 添加PostgreSQL插件
4. 配置环境变量
5. 部署

#### 2.3 Heroku

1. 在 [https://heroku.com](https://heroku.com) 注册账号
2. 创建新应用
3. 添加PostgreSQL插件
4. 配置Procfile：
   ```
   web: gunicorn apps.tcm.wsgi:application --bind 0.0.0.0:$PORT --workers 4
   ```
5. 部署

---

### 方案三：容器化部署（使用systemd）

#### 3.1 使用systemd管理（推荐）

创建 `/etc/systemd/system/tcm-agent.service`（同方案一）

创建 `/etc/systemd/system/tcm-postgres.service`：

```ini
[Unit]
Description=TCM Agent PostgreSQL
After=network.target

[Service]
User=postgres
ExecStart=/usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/data
ExecStop=/usr/lib/postgresql/16/bin/pg_ctl stop -D /var/lib/postgresql/data
Type=notify
PIDFile=/var/run/postgresql/postgresql.pid
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable tcm-postgres
sudo systemctl start tcm-postgres
```

#### 3.2 使用Supervisor管理

安装Supervisor：
```bash
sudo apt install -y supervisor
```

创建配置文件 `/etc/supervisor/conf.d/tcm-agent.conf`：

```ini
[program:tcm-agent]
command=/path/to/tcm-agent-system/venv/bin/gunicorn apps.tcm.wsgi:application --bind 0.0.0.0:8000 --workers 4
directory=/path/to/tcm-agent-system
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/tcm-agent/supervisor.err.log
stdout_logfile=/var/log/tcm-agent/supervisor.out.log
```

启动：
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start tcm-agent
```

---

### 方案四：本地开发部署

#### 4.1 使用uvicorn（开发环境）

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装uvicorn（可选，更快的ASGI服务器）
pip install uvicorn

# 启动开发服务器
uvicorn apps.tcm.asgi:application --host 0.0.0.0 --port 8000 --reload
```

#### 4.2 使用manage.py runserver

```bash
python manage.py runserver 0.0.0.0:8000
```

---

### 部署检查清单

#### 部署前检查

- [ ] 数据库配置正确
- [ ] 环境变量已设置
- [ ] PostgreSQL扩展已安装（vector）
- [ ] 数据库迁移已完成
- [ ] 静态文件已收集
- [ ] SECRET_KEY已设置
- [ ] DEBUG设置为False

#### 部署后验证

- [ ] 应用可以访问
- [ ] 数据库连接正常
- [ ] 静态文件加载正常
- [ ] 知识库功能正常
- [ ] 聊天功能正常

---

### 常见问题排查

#### 数据库连接问题
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 检查PostgreSQL日志
sudo tail -f /var/log/postgresql/postgresql.log

# 测试数据库连接
python manage.py dbshell
```

#### 应用日志查看
```bash
# 查看Gunicorn日志
sudo tail -f /var/log/tcm-agent/error.log

# 查看应用日志
python manage.py shell -c "from apps.knowledge.models import Document; print(Document.objects.all())"
```

#### 性能优化建议

1. **数据库优化**
   - 为embedding列创建索引
   - 为knowledge_id列创建索引
   - 配置PostgreSQL连接池

2. **缓存优化**
   - 配置Redis缓存
   - 使用Django缓存框架

3. **静态文件优化**
   - 使用CDN托管静态文件
   - 启用gzip压缩

4. **Worker配置**
   - 根据服务器配置调整worker数量
   - 推荐worker数量 = (CPU核心数 * 2) + 1

---

### 安全建议

1. **防火墙配置**
   ```bash
   sudo ufw allow 8000/tcp
   sudo ufw allow 5432/tcp
   ```

2. **HTTPS配置**
   - 使用Let's Encrypt免费SSL证书
   - 配置Nginx SSL重定向

3. **环境变量保护**
   - 不要在代码中硬编码密钥
   - 使用.env文件管理敏感信息
   - 将.env添加到.gitignore

4. **定期更新**
   - 定期更新依赖包
   - 及时应用安全补丁
   - 定期备份数据库

---

### 监控建议

1. **应用监控**
   - 使用Sentry进行错误追踪
   - 配置健康检查端点
   - 监控应用性能指标

2. **日志监控**
   - 配置日志轮转
   - 使用日志分析工具（如ELK）
   - 设置告警规则

---

### 备份策略

1. **数据库备份**
   ```bash
   # 每日备份
   pg_dump -U postgres tcm_agent_db > backup_$(date +%Y%m%d).sql
   ```

2. **应用备份**
   - 定期备份media文件
   - 备份配置文件

3. **代码备份**
   - 使用Git进行版本控制
   - 定期打标签

---

## 快速开始

如果您想快速开始，推荐使用**方案一（传统服务器部署）**：

```bash
# 1. 克隆项目
git clone <your-repo-url> tcm-agent-system
cd tcm-agent-system

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境
cp .env.example .env
nano .env  # 编辑配置

# 5. 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 6. 创建超级用户（首次部署）
python manage.py createsuperuser

# 7. 使用systemd启动（参考方案一）
# 或使用gunicorn直接启动
gunicorn apps.tcm.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## 需要帮助？

如果您在部署过程中遇到任何问题，请提供：
1. 错误信息
2. 使用的部署方案
3. 服务器环境（操作系统、云服务商等）
4. 具体的错误日志

我会根据您的具体情况提供针对性的解决方案！
