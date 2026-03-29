# 中医智能问诊系统 - 完整架构文档

## 项目概述

本项目是一个基于 Vue.js + Django 的中医智能问诊系统，采用多智能体架构进行中医辨证分型和调理建议生成。

### 技术栈
- **前端**: Vue.js 3 + TypeScript + Element Plus + Pinia + Vite
- **后端**: Django 4 + DRF + JWT + Pydantic + SQLite/PostgreSQL
- **AI**: 多智能体架构（基于 LLM 的 Agent 协作）
- **存储**: SQLite (开发) / PostgreSQL (生产) + Redis (可选)

---

## 1. 项目目录结构

```
Tcm-agent-system/
├── apps/                          # 后端 Django 应用
│   ├── agents/                    # 多智能体核心模块
│   ├── application/               # 应用配置管理
│   ├── chat/                      # 聊天功能
│   ├── common/                    # 公共工具
│   ├── knowledge/                 # 知识库管理
│   ├── model_provider/            # 模型提供者
│   ├── tcm/                       # Django 项目配置
│   ├── tools/                     # 工具函数
│   └── users/                     # 用户管理
├── ui/                            # 前端 Vue 项目
│   ├── src/
│   │   ├── api/                   # API 接口封装
│   │   ├── components/            # 公共组件
│   │   ├── router/                # 路由配置
│   │   ├── utils/                 # 工具函数
│   │   └── views/                 # 页面视图
│   ├── package.json
│   └── vite.config.ts
├── models/                        # 本地模型存储
├── backup/                        # 备份文件
├── logs/                          # 日志文件
├── manage.py                      # Django 管理脚本
├── requirements.txt               # Python 依赖
└── docker-compose.yml             # Docker 配置
```

---

## 2. 后端架构

### 2.1 多智能体系统 (apps/agents/)

这是项目的核心，实现了中医问诊的多智能体协作流程。

#### 核心文件:
```
agents/
├── orchestrator.py           # 主协调器 - 管理整个流程
├── session_state.py          # 会话状态管理 - 统一状态机
├── intake_agent.py           # 接诊分诊 Agent
├── inquiry_agent.py          # 追问引导 Agent
├── observation_agent.py      # 望诊分析 Agent
├── syndrome_agent.py         # 辨证分型 Agent
├── recommendation_agent.py   # 调理建议 Agent
├── safety_agent.py           # 安全审查 Agent
├── report_agent.py           # 报告生成 Agent
├── wellness_agent.py         # 养生规划 Agent
├── views.py                  # API 接口
├── urls.py                   # 路由配置
└── models.py                 # 数据库模型
```

#### 核心类:
- **Orchestrator**: 主协调器，管理整个问诊流程
- **SessionState**: 会话状态机，在各 Agent 之间传递上下文
- **BaseAgent**: 基础 Agent 类，提供通用功能
- **各具体 Agent**: 实现特定功能的智能体

#### 会话状态模型:
```python
class ConsultStage(str, Enum):
    INTAKE = "intake"               # 接诊分诊
    INQUIRY = "inquiry"             # 十问追问
    OBSERVATION = "observation"     # 望诊融合
    SYNDROME = "syndrome"           # 辨证分型
    RECOMMENDATION = "recommendation"  # 调理建议
    SAFETY_CHECK = "safety_check"   # 安全审查
    REPORT = "report"               # 报告生成
    DONE = "done"                   # 完成
```

### 2.2 用户管理 (apps/users/)

```
users/
├── views/
│   ├── login.py              # 登录注册
│   └── profile.py            # 用户档案
├── models.py                 # 用户模型
├── urls.py                   # 用户路由
└── serializers.py            # 序列化器
```

### 2.3 知识库管理 (apps/knowledge/)

```
knowledge/
├── views.py                  # 知识库 CRUD
├── models.py                 # 知识库模型
├── serializers.py            # 序列化器
└── vector_search.py          # 向量搜索
```

### 2.4 聊天功能 (apps/chat/)

```
chat/
├── views.py                  # 聊天接口
├── models.py                 # 聊天模型
├── serializers.py            # 序列化器
└── websocket.py              # WebSocket 支持
```

---

## 3. 前端架构

### 3.1 核心文件:

```
ui/src/
├── main.ts                   # 应用入口
├── App.vue                   # 根组件
├── router/index.ts           # 路由配置
├── api/index.ts              # API 接口封装
├── utils/
│   ├── request.ts            # Axios 请求封装
│   └── token.ts              # Token 管理
├── views/
│   ├── Layout.vue            # 主布局
│   ├── Home.vue              # 首页
│   ├── Login.vue             # 登录页
│   ├── Profile.vue           # 用户档案
│   ├── consult/Index.vue     # 问诊主界面
│   ├── consult/Tongue.vue    # 舌象分析
│   ├── wellness/Index.vue    # 养生管理
│   └── knowledge/Index.vue   # 知识库
└── components/
    ├── chat-input/ChatInput.vue  # 聊天输入组件
    └── app-icon/AppIcon.vue      # 图标组件
```

### 3.2 路由结构:

- `/home` - 首页
- `/consult` - 多智能体问诊主界面
- `/consult/tongue` - 舌象分析页面
- `/wellness` - 养生管理
- `/knowledge` - 知识库
- `/profile` - 用户档案
- `/login` - 登录页面

### 3.3 状态管理:

- **Pinia**: 已配置但未使用
- **localStorage**: 主要存储方式
- **window 事件**: 用于组件间通信
- **JWT Token**: 用户认证状态

---

## 4. API 接口

### 4.1 多智能体问诊接口:

- `POST /api/v2/consult/message/stream/` - 流式问诊
- `GET /api/v2/consult/session/{session_id}/` - 获取会话
- `POST /api/v2/consult/image/` - 舌象分析

### 4.2 用户接口:

- `POST /api/auth/login/` - 用户登录
- `POST /api/auth/register/` - 用户注册
- `GET /api/auth/profile/` - 获取用户档案
- `GET /api/auth/archives/` - 获取问诊记录

### 4.3 养生接口:

- `POST /api/v2/consult/wellness/checkin/` - 养生打卡
- `GET /api/v2/consult/wellness/reports/` - 养生报告

---

## 5. 数据库模型

### 5.1 用户模型:

- `User` - Django 内置用户模型
- `UserProfile` - 用户档案扩展

### 5.2 问诊模型:

- `ConsultationSession` - 问诊会话
- `ConsultationMessage` - 问诊消息
- `WellnessArchive` - 养生档案
- `TongueAnalysisArchive` - 舌象分析档案

### 5.3 知识库模型:

- `KnowledgeBase` - 知识库
- `Document` - 知识文档

---

## 6. 核心功能模块

### 6.1 问诊流程:

1. **接诊分诊 (IntakeAgent)** - 接收用户症状描述
2. **追问引导 (InquiryAgent)** - 通过十问收集详细信息
3. **望诊分析 (ObservationAgent)** - 分析舌象图片
4. **辨证分型 (SyndromeAgent)** - 进行中医辨证
5. **调理建议 (RecommendationAgent)** - 生成调理建议
6. **安全审查 (SafetyAgent)** - 检查内容安全性
7. **报告生成 (ReportAgent)** - 生成完整报告

### 6.2 舌象分析:

- 支持图片上传和摄像头拍照
- 基于视觉模型分析舌象特征
- 生成舌象诊断报告

### 6.3 养生管理:

- 养生计划生成
- 养生打卡功能
- 健康数据统计

---

## 7. 部署和运行

### 7.1 开发环境:

```bash
# 后端
python manage.py runserver

# 前端
cd ui && npm run dev
```

### 7.2 生产环境:

```bash
# 使用 Docker
docker-compose up -d
```

---

## 8. 已知问题和改进点

### 8.1 已修复问题:

- ✅ 问诊流程中的重复问题
- ✅ 舌象分析结果为空
- ✅ 养生计划体质推荐
- ✅ 打卡功能异常
- ✅ JWT Token 处理

### 8.2 待改进:

- 🔧 Pinia 状态管理未使用
- 🔧 部分 API 错误处理
- 🔧 流式响应稳定性
- 🔧 前端组件复用性

---

## 9. 开发指南

### 9.1 添加新功能:

1. 在 `apps/agents/` 中添加新 Agent
2. 在 `orchestrator.py` 中注册 Agent
3. 在前端添加对应的 API 调用
4. 在 Vue 组件中实现 UI

### 9.2 修改流程:

1. 修改 `orchestrator.py` 中的流程控制
2. 修改对应 Agent 的逻辑
3. 更新前端流程展示

### 9.3 调试技巧:

- 使用浏览器开发者工具查看网络请求
- 使用 Django 日志查看后端调试信息
- 使用 Vue 开发者工具查看组件状态
