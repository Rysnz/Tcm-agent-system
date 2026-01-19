# 本地服务器部署指南

## 前提条件

1. ✅ 已安装Python 3.11
2. ✅ 已安装Node.js
3. ✅ 已安装PostgreSQL（支持pgvector扩展）
4. ✅ 项目代码已准备好

---

## 部署方案一：使用systemd管理（推荐）

### 步骤1：准备项目文件

#### 1.1 创建环境变量文件

创建 `.env` 文件：

```env
# 数据库配置
POSTGRES_DB=tcm_agent_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Django配置
DJANGO_SETTINGS_MODULE=apps.tcm.settings
DJANGO_SECRET_KEY=your-production-secret-key-change-this
DEBUG=False

# Hugging Face配置（可选）
HF_ENDPOINT=https://hf-mirror.com

# 模型API配置（可选）
LLM_API_KEY=your-model-api-key
LLM_BASE_URL=https://api.xiaomimimo.com/v1/chat/completions

# 服务器配置
ALLOWED_HOSTS=your-domain.com,your-ip-address
```

#### 1.2 创建systemd服务文件

创建 `/etc/systemd/system/tcm-agent.service`：

```ini
[Unit]
Description=TCM Agent System Django Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/tcm-agent-system
Environment="PATH=/path/to/tcm-agent-system/venv/bin:/usr/bin:/bin"
ExecStart=/path/to/tcm-agent-system/venv/bin/gunicorn \
    apps.tcm.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1200 \
    --max-requests-jitter 50 \
    --timeout 120 \
    --keepalive 5 \
    --access-logfile /var/log/tcm-agent/access.log \
    --error-logfile /var/log/tcm-agent/error.log \
    --log-level info

[Install]
WantedBy=multi-user.target

[Install]
WantedBy=multi-user.target
```

---

### 步骤2：配置PostgreSQL

#### 2.1 创建PostgreSQL服务文件

创建 `/etc/systemd/system/tcm-postgres.service`：

```ini
[Unit]
Description=TCM Agent PostgreSQL Database
After=network.target

[Service]
Type=notify
User=postgres
ExecStart=/usr/lib/postgresql/16/bin/postgres -D /var/lib/postgresql/data
ExecStop=/usr/lib/postgresql/16/bin/pg_ctl stop -D /var/lib/postgresql/data
ExecReload=/usr/lib/postgresql/16/bin/pg_ctl reload -D /var/lib/postgresql/data
Type=notify
PIDFile=/var/run/postgresql/postgresql.pid
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2.2 配置PostgreSQL

```bash
# 切换到postgres用户
sudo -i -u postgres psql

# 创建数据库
CREATE DATABASE tcm_agent_db;

# 创建用户
CREATE USER tcm_user WITH PASSWORD 'your_secure_password_here';

# 授予权限
GRANT ALL PRIVILEGES ON DATABASE tcm_agent_db TO tcm_user;

# 启用pgvector扩展
\c tcm_agent_db
CREATE EXTENSION IF NOT EXISTS vector;

# 退出
\q
```

#### 2.3 配置pg_hba.conf（可选）

编辑 `/etc/postgresql/16/main/pg_hba.conf`，添加：

```
# IPv4 local connections:
host    all             all             127.0.0.1/32            scram-sha-256
host    all             all             ::1/128                 scram-sha-256

# IPv4 local connections:
host    tcm_agent_db   tcm_user         127.0.0.1/32            scram-sha-256
host    tcm_agent_db   tcm_user         ::1/128                 scram-sha-256
```

重启PostgreSQL：
```bash
sudo systemctl daemon-reload
sudo systemctl restart postgresql
```

---

### 步骤3：配置Django应用

#### 3.1 创建虚拟环境

```bash
cd /path/to/tcm-agent-system
python3 -m venv venv
source venv/bin/activate
```

#### 3.2 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3.3 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 3.4 收集静态文件

```bash
python manage.py collectstatic --noinput
```

#### 3.5 创建超级用户（首次部署）

```bash
python manage.py createsuperuser
```

按照提示输入：
- 用户名：admin
- 邮箱：admin@example.com
- 密码：设置一个强密码

---

### 步骤4：启动服务

#### 4.1 启动PostgreSQL

```bash
sudo systemctl daemon-reload
sudo systemctl enable tcm-postgres
sudo systemctl start tcm-postgres
```

验证PostgreSQL状态：
```bash
sudo systemctl status postgresql
```

#### 4.2 启动Django应用

```bash
sudo systemctl daemon-reload
sudo systemctl enable tcm-agent
sudo systemctl start tcm-agent
```

验证应用状态：
```bash
sudo systemctl status tcm-agent
```

#### 4.3 查看日志

```bash
# 查看应用日志
sudo journalctl -u tcm-agent -f

# 查看最近100行
sudo journalctl -u tcm-agent -n 100

# 查看错误日志
sudo tail -f /var/log/tcm-agent/error.log

# 查看访问日志
sudo tail -f /var/log/tcm-agent/access.log
```

---

### 步骤5：配置Nginx（可选，推荐）

#### 5.1 创建Nginx配置文件

创建 `/etc/nginx/sites-available/tcm-agent`：

```nginx
server {
    listen 80;
    server_name your-domain.com your-ip-address;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $scheme;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }

    location /static/ {
        alias /path/to/tcm-agent-system/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/tcm-agent-system/media;
        expires 30d;
    }

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/rss+xml;
    gzip_comp_level 6;
}
```

#### 5.2 启用配置

```bash
sudo ln -s /etc/nginx/sites-available/tcm-agent /etc/nginx/sites-enabled/
sudo nginx -t
```

#### 5.3 测试Nginx配置

```bash
sudo nginx -t
```

---

### 步骤6：使用Supervisor管理（可选，推荐）

如果需要更灵活的进程管理，可以使用Supervisor：

#### 6.1 安装Supervisor

```bash
sudo apt update
sudo apt install -y supervisor
```

#### 6.2 创建Supervisor配置

创建 `/etc/supervisor/conf.d/tcm-agent.conf`：

```ini
[program:tcm-agent]
command=/path/to/tcm-agent-system/venv/bin/gunicorn \
    apps.tcm.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1200 \
    --max-requests-jitter 50 \
    --timeout 120 \
    --keepalive 5 \
    --access-logfile /var/log/tcm-agent/supervisor-access.log \
    --error-logfile /var/log/tcm-agent/supervisor-error.log \
    --log-level info \
    --user www-data
directory=/path/to/tcm-agent-system
autostart=true
autorestart=true
startretries=3
stopwaitsecs=10
```

#### 6.3 启动Supervisor

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start tcm-agent
```

---

## 部署方案二：使用PM2管理（Node.js项目）

如果需要同时管理前端和后端：

### 步骤1：安装PM2

```bash
npm install -g pm2
```

### 步骤2：创建PM2配置

创建 `ecosystem.config.js`：

```javascript
module.exports = {
  apps: [
    {
      name: 'tcm-backend',
      script: 'venv/bin/gunicorn apps.tcm.wsgi:application --bind 0.0.0.0:8000 --workers 4',
      interpreter: 'python3',
      cwd: '/path/to/tcm-agent-system',
      env_file: '.env',
      instances: 1,
      autorestart: true,
      max_memory_restart: '1G',
      error_file: '/var/log/tcm-agent/pm2-error.log',
      out_file: '/var/log/tcm-agent/pm2-out.log',
      merge_logs: true
    }
  ]
};
```

### 步骤3：启动服务

```bash
pm2 start
```

### 步骤4：管理服务

```bash
# 查看状态
pm2 status

# 查看日志
pm2 logs

# 重启服务
pm2 restart tcm-backend

# 停止服务
pm2 stop tcm-backend
```

---

## 部署方案三：使用Docker Compose（推荐）

如果想要容器化部署：

### 步骤1：创建docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: tcm-postgres
    environment:
      POSTGRES_DB: tcm_agent_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres123
      POSTGRES_HOST_AUTH_METHOD: trust
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres123
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - DJANGO_SETTINGS_MODULE=apps.tcm.settings
      - DJANGO_SECRET_KEY=django-insecure-change-this-in-production
      - DEBUG=False
      - HF_ENDPOINT=https://hf-mirror.com
    depends_on:
      - postgres
    volumes:
      - ./apps:/app
    restart: unless-stopped

volumes:
  postgres_data:
```

### 步骤2：启动服务

```bash
docker-compose up -d
```

### 步骤3：管理服务

```bash
# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart backend

# 停止服务
docker-compose down

# 查看状态
docker-compose ps
```

---

## 部署方案四：使用Gunicorn直接运行（开发环境）

### 步骤1：启动开发服务器

```bash
cd /path/to/tcm-agent-system
source venv/bin/activate

# 使用gunicorn
gunicorn apps.tcm.wsgi:application --bind 0.0.0.0:8000 --workers 4

# 或使用uvicorn（更快的ASGI服务器）
pip install uvicorn
uvicorn apps.tcm.asgi:application --host 0.0.0.0 --port 8000 --reload
```

### 步骤2：使用manage.py runserver

```bash
python manage.py runserver 0.0.0.0:8000
```

---

## 部署检查清单

### 部署前检查

- [ ] 数据库配置正确（.env文件）
- [ ] PostgreSQL扩展已安装（vector）
- [ ] 数据库迁移已完成
- [ ] 静态文件已收集
- [ ] SECRET_KEY已设置
- [ ] DEBUG设置为False
- [ ] ALLOWED_HOSTS已配置

### 部署后验证

- [ ] 应用可以访问
- [ ] 数据库连接正常
- [ ] 静态文件加载正常
- [ ] 知识库功能正常
- [ ] 聊天功能正常

---

## 常见问题排查

### 问题1：应用无法启动

```bash
# 检查systemd服务状态
sudo systemctl status tcm-agent

# 查看日志
sudo journalctl -u tcm-agent -n 50

# 检查端口占用
sudo netstat -tlnp | grep 8000
```

### 问题2：数据库连接失败

```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 检查数据库连接
python manage.py dbshell

# 检查pg_hba.conf
cat /etc/postgresql/16/main/pg_hba.conf
```

### 问题3：静态文件404

```bash
# 检查静态文件目录
ls -la /path/to/tcm-agent-system/static/

# 检查settings.py
grep STATIC_ROOT apps/tcm/settings.py

# 手动收集
python manage.py collectstatic --noinput --clear
```

### 问题4：权限问题

```bash
# 检查文件权限
ls -la /path/to/tcm-agent-system/media/

# 修改权限
sudo chown -R www-data:www-data /path/to/tcm-agent-system/media/
sudo chmod -R 755 /path/to/tcm-agent-system/media/
```

---

## 性能优化建议

### 1. 数据库优化

```sql
-- 为embedding列创建索引
CREATE INDEX CONCURRENTLY tcm_embedding_idx_knowledge_id ON tcm_embedding(knowledge_id);

-- 为knowledge_id列创建索引
CREATE INDEX CONCURRENTLY tcm_embedding_knowledge_id_idx ON tcm_embedding(knowledge_id);

-- 为paragraph_id列创建索引
CREATE INDEX CONCURRENTLY tcm_embedding_paragraph_id_idx ON tcm_embedding(paragraph_id);
```

### 2. 缓存优化

```python
# 在settings.py中配置Redis缓存
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 3. 静态文件优化

```nginx
# 启用gzip压缩
gzip on;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript;
gzip_comp_level 6;

# 设置缓存头
expires 30d;
add_header Cache-Control "public, immutable";
```

### 4. Worker配置

```ini
# 根据服务器配置调整worker数量
# 推荐公式：workers = (CPU核心数 * 2) + 1

# 例如：4核CPU
workers = 9

# 2核CPU
workers = 5
```

---

## 安全建议

### 1. 防火墙配置

```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp
sudo ufw allow 5432/tcp
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --permanent --add-port=5432/tcp
sudo firewall-cmd --reload
```

### 2. HTTPS配置

```bash
# 使用Let's Encrypt免费SSL证书
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 3. 环境变量保护

```bash
# 不要在代码中硬编码密钥
# 使用.env文件
# 将.env添加到.gitignore

# 设置文件权限
chmod 600 .env
```

---

## 监控建议

### 1. 应用监控

```bash
# 使用systemd查看资源使用
systemctl status tcm-agent

# 查看CPU和内存
top -p $(pgrep -f tcm-agent)
```

### 2. 日志监控

```bash
# 配置日志轮转
# 在systemd服务文件中添加
LimitNOFILE=1048576
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=tcm-agent

# 使用logrotate
sudo apt install -y logrotate
```

---

## 备份策略

### 1. 数据库备份

```bash
# 创建备份脚本
cat > /path/to/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d)
pg_dump -U postgres tcm_agent_db | gzip > $BACKUP_DIR/tcm_agent_db_$DATE.sql.gz
find $BACKUP_DIR -name "tcm_agent_db_*.sql.gz" -mtime +30 -delete
EOF

chmod +x /path/to/backup-db.sh

# 添加到crontab
crontab -e
0 2 * * * /path/to/backup-db.sh
```

### 2. 应用备份

```bash
# 备份media文件
rsync -avz /path/to/tcm-agent-system/media/ /path/to/backups/media/

# 备份配置文件
rsync -avz /path/to/tcm-agent-system/.env /path/to/backups/env/
```

---

## 快速开始

### 最简单的部署流程（systemd + Gunicorn）

```bash
# 1. 创建.env文件
cat > .env << 'EOF'
POSTGRES_DB=tcm_agent_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DJANGO_SETTINGS_MODULE=apps.tcm.settings
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
EOF

# 2. 创建systemd服务文件
sudo tee /etc/systemd/system/tcm-agent.service > /dev/null << 'EOF'
[Unit]
Description=TCM Agent System
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/tcm-agent-system
ExecStart=/path/to/tcm-agent-system/venv/bin/gunicorn apps.tcm.wsgi:application --bind 0.0.0.0:8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 3. 配置PostgreSQL
sudo -i -u postgres psql -c "CREATE DATABASE tcm_agent_db; CREATE EXTENSION vector;"

# 4. 安装依赖并迁移
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate

# 5. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable tcm-agent
sudo systemctl start tcm-agent

# 6. 查看日志
sudo journalctl -u tcm-agent -f
```

---

## 需要帮助？

如果在部署过程中遇到任何问题，请提供：
1. 错误信息（systemd日志、应用日志）
2. 使用的部署方案（systemd、Docker Compose、PM2等）
3. 服务器环境（操作系统、Python版本等）
4. 具体的错误堆栈

我会根据您的具体情况提供针对性的解决方案！
