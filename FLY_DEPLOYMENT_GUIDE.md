# 飞牛OS 部署指南

## 前提条件

1. 已安装 [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/)
2. 已注册 [Fly.io](https://fly.io/) 账号
3. 项目代码已推送到Git仓库（GitHub、GitLab等）

---

## 部署步骤

### 步骤1：安装Fly CLI

#### Windows系统
```powershell
# 使用PowerShell安装
iwr -usegetbin-community https://fly.io/install.ps1 | iex
```

#### macOS/Linux系统
```bash
# 使用curl安装
curl -L https://fly.io/install.sh | sh
```

#### 验证安装
```bash
flyctl version
```

---

### 步骤2：登录Fly账号

```bash
flyctl auth login
```

按照提示输入：
- 如果是第一次登录，会打开浏览器进行OAuth授权
- 如果已登录，会显示当前账号信息

---

### 步骤3：初始化Fly应用

```bash
# 在项目根目录执行
fly launch
```

按照提示选择：
1. **组织**：选择或创建您的组织
2. **区域**：选择离您最近的区域（推荐：香港、新加坡、东京等）
3. **应用名称**：输入应用名称（如：tcm-agent-system）
4. **部署区域**：选择部署区域
5. **数据库**：选择PostgreSQL（推荐）

Fly会自动：
- 创建`fly.toml`配置文件
- 配置PostgreSQL数据库
- 设置环境变量
- 部署应用

---

### 步骤4：配置应用（如果需要）

如果`fly launch`没有自动创建`fly.toml`，或者需要自定义配置，手动创建：

```bash
# 创建fly.toml文件
cat > fly.toml << 'EOF'
app = "tcm-agent-system"
primary_region = "hkg"

[build]
  dockerfile = "Dockerfile"

[env]
  DJANGO_SETTINGS_MODULE = "apps.tcm.settings"
  DJANGO_SECRET_KEY = "django-insecure-change-this-in-production"
  DEBUG = "False"
  HF_ENDPOINT = "https://hf-mirror.com"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true

[checks]
  [checks.http]
    port = 8000
    type = "tcp"
    interval = "15s"
    timeout = "10s"
EOF
```

---

### 步骤5：推送代码到Git仓库

#### 如果代码还没有在Git仓库

```bash
# 初始化Git仓库
git init

# 添加所有文件
git add .

# 首次提交
git commit -m "Initial commit"

# 添加远程仓库
git remote add origin https://github.com/your-username/tcm-agent-system.git

# 推送代码
git push -u origin main
```

#### 如果代码已在Git仓库

```bash
# 拉取最新代码
git pull origin main

# 添加修改的文件
git add .

# 提交更改
git commit -m "Update deployment configuration"

# 推送代码
git push origin main
```

---

### 步骤6：部署应用

#### 方法一：使用Fly CLI自动部署

```bash
# 在项目根目录执行
fly deploy
```

Fly会自动：
1. 检测到`fly.toml`文件
2. 读取配置
3. 构建Docker镜像
4. 推送到Fly.io
5. 启动应用

#### 方法二：手动部署

```bash
# 创建应用
fly apps create tcm-agent-system

# 设置环境变量
flyctl secrets set DJANGO_SECRET_KEY "your-secret-key-here"
flyctl secrets set POSTGRES_PASSWORD "your-secure-password"

# 部署
fly deploy
```

---

### 步骤7：数据库迁移

首次部署时，Fly会自动运行数据库迁移：

```bash
# 手动运行迁移（如果需要）
flyctl ssh console
cd /app
python manage.py makemigrations
python manage.py migrate
```

或者通过应用日志监控迁移执行情况：

```bash
# 查看应用日志
flyctl logs

# 进入应用控制台
flyctl dashboard
```

---

### 步骤8：收集静态文件（如果需要）

Fly会自动收集静态文件，但如果需要手动操作：

```bash
# 在本地运行
python manage.py collectstatic --noinput

# 提交静态文件
git add static/
git commit -m "Add static files"
git push origin main
```

---

### 步骤9：配置环境变量（重要）

#### 通过Fly CLI设置

```bash
# 设置Django密钥
flyctl secrets set DJANGO_SECRET_KEY "your-production-secret-key"

# 设置数据库密码
flyctl secrets set POSTGRES_PASSWORD "your-secure-password"

# 设置Hugging Face镜像源（可选）
flyctl secrets set HF_ENDPOINT "https://hf-mirror.com"

# 设置模型API密钥
flyctl secrets set LLM_API_KEY "your-model-api-key"

# 设置模型API地址
flyctl secrets set LLM_BASE_URL "https://api.xiaomimimo.com/v1/chat/completions"

# 查看所有密钥
flyctl secrets list
```

#### 通过Fly Dashboard设置

1. 访问 [https://fly.io/dashboard](https://fly.io/dashboard)
2. 选择您的应用
3. 点击"Settings" → "Secrets"
4. 添加上述环境变量

---

### 步骤10：监控应用

#### 查看应用状态

```bash
# 查看应用状态
flyctl status

# 查看应用信息
flyctl info

# 查看应用列表
flyctl apps list
```

#### 查看应用日志

```bash
# 实时查看日志
flyctl logs

# 查看最近100行日志
flyctl logs --lines 100

# 查看特定机器的日志
flyctl logs --machine <machine-id>

# 持续查看日志
flyctl logs --tail
```

#### 访问应用控制台

访问：[https://fly.io/dashboard](https://fly.io/dashboard)

可以查看：
- 应用状态
- 机器状态
- 资源使用情况
- 部署历史
- 日志

---

### 步骤11：访问应用

#### 获取应用URL

```bash
# 查看应用URL
flyctl info

# 输出示例：
App Name: tcm-agent-system
Hostname: tcm-agent-system.fly.dev
Deployed: true
```

#### 访问应用

- **API端点**：`https://tcm-agent-system.fly.dev/api/`
- **管理后台**：`https://tcm-agent-system.fly.dev/admin/`
- **前端**：如果配置了前端，访问对应URL

---

### 步骤12：配置自定义域名（可选）

#### 方法一：通过Fly CLI

```bash
# 添加自定义域名
flyctl certs add your-domain.com

# 设置主域名
flyctl ips allocate-v4

# 绑定域名
flyctl launch --ha
```

#### 方法二：通过Dashboard

1. 访问Fly Dashboard
2. 选择应用 → "Settings" → "Domains"
3. 添加自定义域名
4. 配置DNS记录

---

### 步骤13：更新应用

#### 更新代码

```bash
# 1. 修改代码
# 2. 提交更改
git add .
git commit -m "Update feature"
git push origin main

# 3. 触发部署
fly deploy
```

#### 回滚部署

```bash
# 查看部署历史
flyctl releases

# 回滚到上一个版本
flyctl releases rollback <version>

# 重新部署特定版本
flyctl deploy --image <image-id>
```

---

### 步骤14：故障排查

#### 应用无法启动

```bash
# 查看应用状态
flyctl status

# 查看机器状态
flyctl machines list

# 重启应用
flyctl apps restart tcm-agent-system

# 查看日志
flyctl logs
```

#### 数据库连接问题

```bash
# 进入应用控制台
flyctl ssh console

# 检查数据库连接
python manage.py dbshell

# 检查PostgreSQL状态
flyctl postgres connect
```

#### 性能问题

```bash
# 查看资源使用情况
flyctl status

# 扩容资源
flyctl scale count 2

# 查看机器规格
flyctl machines show
```

---

## 飞牛OS配置说明

### fly.toml 配置选项

```toml
app = "tcm-agent-system"
primary_region = "hkg"  # 主区域：香港、新加坡、东京等

[build]
  dockerfile = "Dockerfile"  # Dockerfile路径
  # 或使用构建命令
  # build_command = "python manage.py collectstatic"

[env]
  # Django配置
  DJANGO_SETTINGS_MODULE = "apps.tcm.settings"
  DJANGO_SECRET_KEY = "django-insecure-change-this-in-production"
  DEBUG = "False"
  
  # Hugging Face配置
  HF_ENDPOINT = "https://hf-mirror.com"
  
  # 模型API配置（可选）
  # LLM_API_KEY = "your-api-key"
  # LLM_BASE_URL = "https://api.xiaomimimo.com/v1/chat/completions"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true

[checks]
  [checks.http]
    port = 8000
    type = "tcp"
    interval = "15s"
    timeout = "10s"
```

### 环境变量说明

| 变量名 | 说明 | 必需 |
|---|---|---|
| DJANGO_SETTINGS_MODULE | Django设置模块 | 是 |
| DJANGO_SECRET_KEY | Django密钥 | 是 |
| DEBUG | 调试模式 | 是 |
| HF_ENDPOINT | Hugging Face镜像源 | 否 |
| POSTGRES_DB | 数据库名 | 自动 |
| POSTGRES_USER | 数据库用户 | 自动 |
| POSTGRES_PASSWORD | 数据库密码 | 自动 |
| POSTGRES_HOST | 数据库主机 | 自动 |
| POSTGRES_PORT | 数据库端口 | 自动 |
| LLM_API_KEY | 模型API密钥 | 否 |
| LLM_BASE_URL | 模型API地址 | 否 |

---

## 成本估算

### 免费额度

- **每月免费额度**：3 GB内存 × 24小时 × 30天
- **数据库**：1 GB共享PostgreSQL
- **带宽**：160 GB/月
- **请求次数**：100,000次/月

### 付费计划

- **Basic**：$5/月（256 MB RAM, 2 vCPU）
- **Standard**：$29/月（1 GB RAM, 2 vCPU, 3 GB存储）
- **Premium**：$93/月（8 GB RAM, 4 vCPU, 40 GB存储）

---

## 最佳实践

### 1. 安全性

- ✅ 使用环境变量存储敏感信息
- ✅ 不要在代码中硬编码密钥
- ✅ 设置`DEBUG=False`在生产环境
- ✅ 使用强密码
- ✅ 定期更新依赖包

### 2. 性能优化

- ✅ 使用Gunicorn作为WSGI服务器
- ✅ 配置适当的worker数量（推荐：2-4个）
- ✅ 设置合理的超时时间（推荐：120秒）
- ✅ 启用数据库连接池
- ✅ 为查询字段创建索引

### 3. 监控

- ✅ 配置健康检查端点
- ✅ 设置日志轮转
- ✅ 使用外部监控服务（如Sentry）
- ✅ 配置告警规则

### 4. 备份

- ✅ 定期备份数据库
- ✅ 备份media文件
- ✅ 使用Git进行版本控制
- ✅ 定期打标签

---

## 常见问题

### Q1: 部署失败怎么办？

```bash
# 查看详细错误信息
flyctl deploy --verbose

# 查看构建日志
flyctl logs --build

# 检查Dockerfile语法
docker build -t test .
```

### Q2: 应用无法访问？

```bash
# 检查应用状态
flyctl status

# 检查健康检查
flyctl checks list

# 查看防火墙规则
flyctl ips list
```

### Q3: 数据库迁移失败？

```bash
# 进入应用控制台
flyctl ssh console

# 手动运行迁移
python manage.py makemigrations
python manage.py migrate
```

### Q4: 如何查看应用日志？

```bash
# 实时查看
flyctl logs

# 查看最近错误
flyctl logs | grep ERROR

# 查看特定时间段
flyctl logs --since 1h
```

---

## 快速开始

### 最简单的部署流程

```bash
# 1. 安装Fly CLI
iwr -usegetbin-community https://fly.io/install.ps1 | iex

# 2. 登录
flyctl auth login

# 3. 初始化应用（会自动创建fly.toml）
fly launch

# 4. 推送代码（如果还没有）
git add .
git commit -m "Initial commit"
git push origin main

# 5. 部署
fly deploy
```

---

## 需要帮助？

如果在部署过程中遇到任何问题，请提供：
1. 错误信息（`flyctl logs`的输出）
2. 使用的部署命令
3. Fly.toml配置内容
4. 服务器环境（操作系统、Fly CLI版本等）

我会根据您的具体情况提供针对性的解决方案！
