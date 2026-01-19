# TCM Agent System - 基于大语言模型的中医智能问诊系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![Django](https://img.shields.io/badge/Django-5.2.9-green.svg)
![React](https://img.shields.io/badge/React-18-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

</div>

## 项目简介

TCM Agent System 是一个结合传统中医理论与现代人工智能技术的创新项目，通过先进的向量检索技术和多模态大语言模型，实现症状分析、体质辨识、辨证论治、方剂推荐等中医特色功能。

## 核心功能

### 知识库管理
- 支持多种文档格式上传（Word、PDF、TXT、Markdown）
- 自动文本提取、分段和向量化
- 向量搜索、关键词搜索、混合搜索三种检索模式
- 实时进度跟踪和状态管理

### 智能问诊
- 多轮对话管理和会话摘要生成
- 流式响应支持（Server-Sent Events）
- 知识库检索集成
- 智能辨证和体质辨识
- 方剂推荐和个性化建议

### 模型管理
- 支持16种大语言模型提供商（OpenAI、DeepSeek、Kimi、Ollama等）
- 统一的模型调用接口
- 动态模型切换和参数配置

## 技术架构

### 后端技术栈
- **框架**：Django 5.2.9
- **语言**：Python 3.11
- **数据库**：PostgreSQL 16 + pgvector
- **向量模型**：SentenceTransformer (shibing624/text2vec-base-chinese, 768维)

### 前端技术栈
- **框架**：React 18 + Vue 3
- **构建工具**：Vite 5
- **UI组件**：Element Plus
- **状态管理**：Pinia
- **HTTP客户端**：Axios

### 部署方式

项目支持多种部署方式，请根据实际需求选择：

1. **本地开发部署**：直接运行开发服务器
   ```bash
   # 后端
   python manage.py runserver
   
   # 前端
   cd ui
   npm run dev
   ```

2. **生产环境部署**：根据实际需求选择
   - 使用Gunicorn + Nginx部署
   - 使用Docker容器化部署
   - 部署到云平台（Fly.io、Render、Railway等）
   
   详细的部署配置请参考项目根目录的部署脚本：
   - `start_all.bat` - 一键启动所有服务
   - `start_backend.bat` - 启动后端
   - `start_frontend.bat` - 启动前端
   - `docker-compose.yml` - Docker容器化部署

## 项目结构

```
tcm-agent-system/
├── apps/                  # Django应用模块
│   ├── tcm/             # 核心配置
│   ├── knowledge/        # 知识库管理
│   ├── chat/             # 聊天对话
│   ├── application/       # 应用管理
│   ├── model_provider/    # 模型提供商
│   ├── users/            # 用户管理
│   ├── tools/            # 工具管理
│   └── system_manage/    # 系统管理
├── ui/                    # 前端代码
│   ├── src/
│   │   ├── views/       # 页面组件
│   │   ├── components/  # 通用组件
│   │   ├── api/         # API接口
│   │   └── router/      # 路由配置
│   └── package.json
├── models/                # 向量模型（已排除）
├── sql/                   # 数据库脚本
├── docker-compose.yml       # Docker配置
├── requirements.txt        # Python依赖
└── manage.py             # Django管理脚本
```

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 16+
- PostgreSQL 16+ (支持pgvector扩展)

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/Rysnz/Tcm-agent-system.git
cd tcm-agent-system
```

2. **安装后端依赖**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **安装前端依赖**
```bash
cd ui
npm install
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，配置数据库连接、API密钥等
```

5. **数据库迁移**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **下载向量模型**
```bash
pip install sentence-transformers
# 模型会自动下载到 models/embedding/ 目录
```

7. **启动服务**
```bash
# 启动后端
python manage.py runserver

# 启动前端（新终端）
cd ui
npm run dev
```

## API接口

### 知识库管理
- `POST /api/knowledge/upload/` - 上传文档
- `GET /api/knowledge/document/` - 查询文档列表
- `POST /api/knowledge/search/` - 向量搜索

### 聊天对话
- `POST /api/chat/stream/` - 流式对话
- `GET /api/chat/session/` - 查询会话列表
- `GET /api/chat/message/` - 查询消息列表

### 模型管理
- `GET /api/model_provider/config/` - 查询模型配置
- `POST /api/model_provider/config/` - 创建模型配置

## 数据库设计

### 核心数据表
- `tcm_knowledge_base` - 知识库
- `tcm_document` - 文档
- `tcm_paragraph` - 段落
- `tcm_embedding` - 向量嵌入（vector(768)类型）
- `tcm_chat_session` - 聊天会话
- `tcm_chat_message` - 聊天消息
- `tcm_application` - 应用
- `tcm_model_config` - 模型配置

## 部署指南

详细的部署指南请参考项目文档：
- 本地部署：systemd服务管理
- Docker部署：Docker Compose配置
- 云平台部署：Fly.io、Render、Railway

## 开发指南

### 代码规范
- 遵循PEP 8 Python编码规范
- 使用类型注解（TypeScript）
- 编写清晰的文档字符串
- 遵循Django最佳实践

### 提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建/工具相关
```

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- **GitHub Issues**：[提交问题和建议](https://github.com/Rysnz/Tcm-agent-system/issues)
- **项目地址**：https://github.com/Rysnz/Tcm-agent-system

## 致谢

感谢所有为本项目提供支持和帮助的开发者！

---

**项目信息**

- **项目名称**：TCM Agent System - 基于大语言模型的中医智能问诊系统
- **开发语言**：Python 3.11
- **后端框架**：Django 5.2.9
- **前端框架**：React 18 + Vite 5
- **数据库**：PostgreSQL 16 + pgvector
- **向量模型**：SentenceTransformer (768维)
- **开发周期**：2025年1月 - 2026年1月

---

**最后更新**：2026年1月19日
