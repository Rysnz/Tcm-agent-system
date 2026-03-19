# 中医智能问诊多智能体系统 — 大模型可读说明文档

> **用途**：本文档供大语言模型（LLM）阅读，用于理解本项目的整体架构、Agent 职责、API 接口、扩展方法、推理轨迹格式等。在此基础上进行代码扩展、功能迭代或二次开发时请以本文档为基准。
>
> **版本**：v2.0（多智能体重构版）

---

## 一、项目概述

**项目名称**：基于大语言模型的中医智能问诊系统（TCM Multi-Agent System）

**毕业设计题目**：基于大语言模型的中医智能问诊系统

**核心创新点**：
1. 多智能体协同实现"望闻问切"完整流程（非单一 prompt 拼接）
2. RAG 混合检索（向量 + BM25 + RRF 融合）增强知识可信度
3. 统一 Pydantic 状态机（`SessionState`）在 Agent 间传递，支持链路追踪
4. 安全审查双保险（关键词快速预检 + LLM 语义审查）
5. 多模态支持：舌象图片 → 结构化特征 → 融入辨证推理

---

## 二、技术栈

| 层次 | 技术选型 |
|------|---------|
| 后端框架 | Python + Django REST Framework |
| LLM 接入 | OpenAI 兼容接口（支持 Qwen / ChatGLM / OpenAI） |
| 向量数据库 | pgvector（PostgreSQL 扩展）或本地 JSON 文件（开发态） |
| 关键词检索 | BM25（自研轻量实现，`apps/knowledge/bm25.py`） |
| 前端框架 | Vue 3 + TypeScript + Element Plus |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） |
| 缓存 | 内存字典（开发）/ Redis（可选，生产） |

---

## 三、项目目录结构

```
Tcm-agent-system/
├── apps/
│   ├── agents/                    # ★ 多智能体系统（核心）
│   │   ├── orchestrator.py        # Agent 编排器
│   │   ├── session_state.py       # 统一会话状态机（Pydantic）
│   │   ├── intake_agent.py        # IntakeAgent：接诊分诊
│   │   ├── inquiry_agent.py       # InquiryAgent：十问追问
│   │   ├── observation_agent.py   # ObservationAgent：望诊融合
│   │   ├── syndrome_agent.py      # SyndromeAgent：辨证分型
│   │   ├── recommendation_agent.py # RecommendationAgent：调理建议
│   │   ├── safety_guard_agent.py  # SafetyGuardAgent：安全审查
│   │   ├── report_agent.py        # ReportAgent：报告生成
│   │   ├── wellness.py            # 个性化养生管理模块
│   │   ├── views.py               # API 端点（Django REST）
│   │   └── urls.py                # 路由：/api/v2/consult/
│   ├── chat/                      # 旧版聊天（保留兼容）
│   ├── knowledge/                 # RAG 知识库管理
│   ├── model_provider/            # LLM 提供商管理
│   ├── users/                     # 认证与用户
│   ├── application/               # 应用配置
│   └── tcm/                       # Django 项目配置（settings, urls）
│       ├── settings.py
│       └── urls.py                # 总路由（含 /api/v2/consult/）
├── ui/                            # ★ 前端（Vue 3 + Element Plus）
│   └── src/
│       ├── views/
│       │   ├── Home.vue           # 首页（系统介绍、功能导航）
│       │   ├── Layout.vue         # 全局布局与顶栏导航
│       │   ├── consult/
│       │   │   ├── Index.vue      # ★ 多智能体问诊主页面
│       │   │   ├── Report.vue     # 问诊报告页
│       │   │   └── Tongue.vue     # 舌象上传分析页
│       │   ├── wellness/
│       │   │   └── Index.vue      # 个性化养生管理页
│       │   ├── chat/Index.vue     # 旧版聊天（保留兼容）
│       │   ├── knowledge/         # 知识库管理
│       │   ├── model/             # 模型管理
│       │   ├── application/       # 应用设置
│       │   └── Overview.vue       # 后台概览
│       ├── api/index.ts           # ★ 所有 API 请求封装（含 consultApi）
│       ├── router/index.ts        # 路由配置
│       └── main.ts                # 入口
├── AGENT_GUIDE.md                 # 本文档
├── README.md                      # 项目说明
├── requirements.txt               # Python 依赖
├── manage.py                      # Django 入口
├── .env.example                   # 环境变量模板
└── docker-compose.yml             # Docker 部署配置
```

---

## 四、启动与部署

### 4.1 后端启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（复制并修改）
cp .env.example .env

# 3. 数据库迁移
python manage.py migrate

# 4. 启动后端（端口 8000）
python manage.py runserver 0.0.0.0:8000
```

**关键环境变量**（`.env` 文件）：
```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
LLM_API_KEY=your-llm-api-key
LLM_API_BASE=https://api.openai.com/v1     # 或兼容接口地址
LLM_MODEL=gpt-4o-mini                       # 或 qwen-turbo 等
DATABASE_URL=sqlite:///db.sqlite3
```

### 4.2 前端启动

```bash
cd ui
npm install
npm run dev          # 开发模式（端口 3000，代理至 localhost:8000）
npm run build        # 生产构建（输出到 ui/dist/）
```

### 4.3 一键启动脚本

```bash
# 同时启动前后端（开发环境）
bash start.sh
```

### 4.4 Docker 部署

```bash
docker-compose up --build -d
```

---

## 五、多智能体系统详解

### 5.1 会话状态机（SessionState）

**文件**：`apps/agents/session_state.py`

```python
class ConsultStage(str, Enum):
    INTAKE = "intake"           # 接诊分诊
    INQUIRY = "inquiry"         # 十问追问
    OBSERVATION = "observation" # 望诊
    SYNDROME = "syndrome"       # 辨证
    RECOMMENDATION = "recommendation"  # 建议
    SAFETY_CHECK = "safety_check"
    REPORT = "report"
    DONE = "done"

class SessionState(BaseModel):
    session_id: str
    trace_id: str
    current_stage: ConsultStage
    messages: List[Message]        # 对话历史
    symptoms: List[Symptom]        # 已收集症状
    patient_profile: PatientProfile # 患者信息
    observation: ObservationData   # 望诊数据
    syndrome_candidates: List[SyndromeCandidate]
    recommendations: List[Recommendation]
    safety_result: SafetyResult
    reference_chunks: List[ReferenceChunk]  # RAG 检索结果
    agent_call_records: List[AgentCallRecord]  # 执行轨迹
    report_text: str
    report_json: dict
    is_high_risk: bool
    disclaimer: str
    created_at: datetime
    updated_at: datetime
```

**状态在 Agent 间以对象引用传递，每个 Agent 读取所需字段并写入输出字段，形成数据流水线。**

### 5.2 Agent 执行流程

```
用户输入
  │
  ▼
SafetyGuardAgent（快速关键词预检）
  │  高风险 → 立即返回就医警告
  ▼
IntakeAgent（收集主诉）
  │  主诉充分 →
  ▼
InquiryAgent（十问追问）
  │  信息足够 →
  ▼
ObservationAgent（融合舌象/图像特征，如有上传）
  │
  ▼
SyndromeAgent（RAG 检索 + LLM 辨证）
  │
  ▼
RecommendationAgent（个性化建议）
  │
  ▼
SafetyGuardAgent（LLM 语义级安全再审）
  │
  ▼
ReportAgent（生成结构化报告）
  │
  ▼
返回前端 ConsultMessageResponse
```

### 5.3 各 Agent 规范

#### IntakeAgent

**职责**：首轮接诊，引导用户描述主诉、病程、既往史、用药史。

**输入**：`SessionState.messages`（含用户最新消息）

**输出**：
- `state.chief_complaint`：主诉文本
- `state.patient_profile`：更新患者信息
- `state.current_stage`：推进或保持 `intake`

**退出条件**：主诉描述充分（判断标准：包含症状+时间信息）

---

#### InquiryAgent

**职责**：按中医"十问"策略动态追问缺失信息。

**十问顺序**（可配置）：
1. 寒热 2. 汗 3. 头身 4. 胸腹 5. 饮食 6. 二便 7. 耳目 8. 睡眠 9. 情志 10. 妇科/儿科

**输入**：`state.symptoms`（已收集），`state.patient_profile`

**输出**：
- `state.symptoms`：追加新症状
- `state.pending_questions`：下一批追问问题
- `state.current_stage`：若信息充分则推进至 `observation`

---

#### ObservationAgent

**职责**：融合文本描述的外观信息和图片舌象特征。

**图片处理流程**：
1. 将图片转为 Base64
2. 调用 LLM 多模态接口提取结构化特征（如 GPT-4V、Qwen-VL）
3. 若 LLM 不支持多模态，使用规则式特征提取（颜色直方图 + 关键词匹配）
4. 将特征写入 `state.observation`

**输入**：`image_bytes`（可选）, `state.messages`（文字描述）

**输出**：
```python
ObservationData(
    tongue_color="淡红",      # 舌色
    tongue_coating="薄白",    # 苔色
    coating_thickness="薄",   # 苔厚薄
    coating_texture="润",     # 苔质
    tongue_shape="正常",      # 舌形
    face_color="正常",        # 面色
    image_features=["舌体胖大", "有齿痕"]  # 视觉特征列表
)
```

---

#### SyndromeAgent

**职责**：综合所有收集到的信息，通过 RAG + LLM 完成辨证分型。

**执行流程**：
1. **Query 重写**：将症状列表重写为检索查询词
2. **混合检索**：向量检索（余弦相似度）+ BM25 关键词检索
3. **RRF 融合**：Reciprocal Rank Fusion 合并两路结果
4. **提示词注入**：将 top-K 片段作为 context 注入 LLM
5. **LLM 推理**：输出候选证型（JSON 结构）

**输出**：
```python
[
    SyndromeCandidate(
        name="脾气虚证",
        confidence=0.85,
        supporting_symptoms=["乏力", "纳差", "便溏"],
        evidence_source="《中医内科学》第5版"
    ),
    SyndromeCandidate(name="肾阳虚证", confidence=0.45, ...),
]
```

---

#### RecommendationAgent

**职责**：基于辨证结果和患者体质，生成可解释的调理建议。

**建议类别**：饮食 / 作息 / 运动 / 情志 / 穴位 / 代茶饮

**限制**：
- 禁止输出具体处方剂量
- 禁止声明"诊断为XX病"
- 所有中草药使用必须附注"请在执业中医师指导下使用"

**输出**：
```python
[
    Recommendation(
        category="饮食",
        content="宜食温补脾胃食物，如山药、莲子、薏苡仁",
        rationale="脾气虚证宜甘温补脾，山药补脾养胃",
        caution="请在执业中医师指导下使用"
    ),
]
```

---

#### SafetyGuardAgent

**职责**：识别高危症状，拦截不当建议，保护特殊人群。

**两级检查**：
1. **关键词快速预检**（毫秒级）：检查高危词库
2. **LLM 语义审查**（慢，按需触发）：判断整体安全性

**高危关键词类别**（`CRITICAL_KEYWORDS`）：
- 心血管：胸痛、心绞痛、心肌梗死、心跳骤停
- 呼吸：呼吸困难、窒息、咯血
- 神经：意识障碍、抽搐、偏瘫
- 消化：便血、呕血、腹膜炎
- 其他：高热 40℃、严重过敏反应

**特殊人群策略**：
- 孕妇：禁止推荐活血化瘀类药物（红花、桃仁等）
- 未成年人：剂量减半提示
- 老年人：避免大剂量苦寒药

**输出**：
```python
SafetyResult(
    risk_level="low"|"medium"|"high"|"critical",
    should_refer_immediately=False,
    safety_message="",
    special_population_flags=["孕妇"],
    modified_recommendations=[]  # 过滤后的建议列表
)
```

---

#### ReportAgent

**职责**：将完整问诊过程整理为结构化报告。

**输出格式**：
```json
{
  "session_id": "...",
  "patient_summary": "...",
  "chief_complaint": "...",
  "inquiry_summary": "...",
  "observation_findings": {...},
  "syndrome_analysis": {
    "primary": "脾气虚证",
    "confidence": 0.85,
    "basis": ["症状列表", "检索依据"]
  },
  "recommendations": [...],
  "safety_notes": "...",
  "disclaimer": "本报告仅供健康参考..."
}
```

---

## 六、API 接口文档

**Base URL**：`/api/v2/consult/`

### 6.1 创建会话

```
POST /api/v2/consult/session/
请求体：{}
响应：{session_id, trace_id, stage, message, disclaimer}
```

### 6.2 发送消息

```
POST /api/v2/consult/message/
请求体：{session_id, message}
响应：{
  session_id, trace_id, stage, is_high_risk,
  assistant_message, pending_questions,
  primary_syndrome, agent_steps,
  report  # 仅在 stage=done 时有值
}
```

### 6.3 上传舌象图片

```
POST /api/v2/consult/image/
Content-Type: multipart/form-data
字段：session_id, image（文件）
响应：{session_id, observation: {...}}
```

### 6.4 获取会话状态

```
GET /api/v2/consult/session/{session_id}/
响应：{session_id, stage, is_high_risk, chief_complaint, ...}
```

### 6.5 获取问诊报告

```
GET /api/v2/consult/session/{session_id}/report/
响应：{session_id, report_text, report_json, disclaimer}
```

### 6.6 获取支持体质列表

```
GET /api/v2/consult/wellness/constitutions/
响应：{constitutions: ["平和质", "气虚质", ...]}
```

### 6.7 生成养生计划

```
POST /api/v2/consult/wellness/plan/
请求体：{constitution, cycle_days, feedback}
响应：{plan: WeeklyWellnessPlan}
```

### 6.8 提交打卡

```
POST /api/v2/consult/wellness/checkin/
请求体：{date, constitution, completed_items, energy_level, sleep_quality, mood_score, notes}
响应：{success: true, message: "..."}
```

---

## 七、RAG 系统

### 7.1 知识库目录结构

```
knowledge_base/
├── classical_texts/     # 《伤寒论》《金匮要略》等经典条文
├── tcm_textbooks/       # 中医内科学、中医诊断学教材摘要
├── syndrome_mapping/    # 证候-症状映射表（JSON）
└── wellness_advice/     # 养生建议库（按体质分类）
```

### 7.2 检索流程

```
用户查询
  │
  ▼
Query 重写（LLM 将口语化症状转为专业术语）
  │
  ├─── 向量检索（OpenAI Embeddings / BGE 嵌入）
  │         余弦相似度 Top-K
  │
  └─── BM25 关键词检索
            BM25 分数 Top-K
  │
  ▼
RRF 融合（Reciprocal Rank Fusion）
  │
  ▼
Cross-Encoder Rerank（可选，提升精度）
  │
  ▼
Top-5 片段注入 LLM 提示词
```

### 7.3 扩展知识库

1. 将文档文件（`.txt`/`.pdf`/`.md`）放入 `knowledge_base/` 对应目录
2. 运行索引构建脚本：
   ```bash
   python manage.py build_knowledge_index --dir knowledge_base/
   ```
3. 索引自动更新，无需重启服务

---

## 八、个性化养生管理

**文件**：`apps/agents/wellness.py`

### 支持的九种体质

| 体质 | 英文标识 | 主要特征 |
|------|---------|---------|
| 平和质 | BALANCED | 体质均衡，身体健康 |
| 气虚质 | QI_DEFICIENCY | 容易疲乏，气短自汗 |
| 阳虚质 | YANG_DEFICIENCY | 怕冷，手足不温 |
| 阴虚质 | YIN_DEFICIENCY | 手足心热，易口干 |
| 痰湿质 | PHLEGM_DAMPNESS | 形体肥胖，腹部松软 |
| 湿热质 | DAMP_HEAT | 面垢油光，易生痤疮 |
| 血瘀质 | BLOOD_STASIS | 肤色晦暗，易有淤斑 |
| 气郁质 | QI_STAGNATION | 情绪不稳，容易焦虑 |
| 特禀质 | SPECIAL | 过敏体质，适应力差 |

### 计划内容

每日计划包含：
- 睡眠建议（睡眠时间、子午觉建议）
- 晨间作息（起床时间、晨练内容）
- 三餐饮食（适宜食物与禁忌）
- 运动建议（强度、项目、时长）
- 情志调节（冥想、音乐疗法等）
- 穴位保健（具体穴位及操作方法）
- 代茶饮（中草药茶方，必须注明需执业中医师指导）

### 反馈规则引擎

用户打卡后，系统记录完成率、能量水平、睡眠质量、情绪分数。下一周期计划生成时，规则引擎根据以下逻辑微调：
- 能量持续低 → 减少运动强度，增加休息建议
- 睡眠质量差 → 强化睡眠相关穴位和茶饮建议
- 情绪评分低 → 增加情志调节内容

---

## 九、前端页面说明

| 路由 | 组件文件 | 功能描述 |
|------|---------|---------|
| `/home` | `views/Home.vue` | 系统首页，功能介绍，Agent 架构可视化 |
| `/consult` | `views/consult/Index.vue` | ★ 多智能体问诊主页（含 Agent 时间线） |
| `/consult/tongue` | `views/consult/Tongue.vue` | 舌象图片上传与分析 |
| `/consult/report` | `views/consult/Report.vue` | 问诊报告展示与导出 |
| `/wellness` | `views/wellness/Index.vue` | 养生计划管理与打卡 |
| `/overview` | `views/Overview.vue` | 后台概览统计 |
| `/application` | `views/application/Setting.vue` | 应用配置（问候语、模型等） |
| `/knowledge` | `views/knowledge/Index.vue` | 知识库管理 |
| `/model` | `views/model/ModelSetting.vue` | LLM 模型提供商配置 |

### 前端 API 封装

所有新版 API 调用通过 `ui/src/api/index.ts` 中的 `consultApi` 对象：

```typescript
import { consultApi } from '@/api'

// 创建会话
const session = await consultApi.createSession()

// 发送消息
const res = await consultApi.sendMessage(sessionId, userMessage)

// 上传舌象
const obs = await consultApi.uploadTongueImage(sessionId, imageFile)

// 生成养生计划
const plan = await consultApi.generateWellnessPlan('气虚质', 7)
```

---

## 十、扩展指南

### 10.1 添加新 Agent

1. 在 `apps/agents/` 创建新文件，如 `diet_agent.py`
2. 继承或参考现有 Agent 结构：
   ```python
   class DietAgent:
       name = "DietAgent"
       
       def run(self, state: SessionState) -> SessionState:
           # 读取 state.syndrome_candidates
           # 调用 LLM 生成饮食建议
           # 写入 state.recommendations
           return state
   ```
3. 在 `orchestrator.py` 的 `_run_pipeline` 方法中插入新 Agent
4. 在前端 `consult/Index.vue` 的 `translateAgent` 函数中添加中文名映射

### 10.2 替换 LLM 提供商

修改 `.env` 文件：
```env
LLM_API_BASE=https://your-provider.com/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model-name
```

系统使用 OpenAI Python SDK，任何兼容 OpenAI 接口的提供商均可直接使用。

### 10.3 扩展知识库

1. 准备文档（`.txt` 或 `.md` 格式）
2. 放入 `knowledge_base/` 对应子目录
3. 运行 `python manage.py build_knowledge_index`
4. 知识将自动被检索系统索引

### 10.4 添加新体质养生规则

在 `apps/agents/wellness.py` 的 `CONSTITUTION_PLANS` 字典中添加对应体质的 `DailyPlan` 模板。

---

## 十一、安全合规说明

### 免责声明（强制显示）

> 本系统输出内容仅为健康建议与中医辨证参考，不构成任何医疗诊断结论，不能替代执业医师的专业诊疗。如有任何疑问或症状较重，请及时前往正规医疗机构就诊。

### 高危拦截策略

系统在以下情况会触发高危警告并拒绝生成建议：
- 提及`CRITICAL_KEYWORDS`中的高危词汇（胸痛、呼吸困难、意识障碍等）
- 孕妇提及流产或出血症状
- 未成年人伴有严重发育异常

### 禁止输出内容

- 明确处方及剂量（"桂枝 10g，炙甘草 6g" 等具体克数）
- 声明"您患有XX病"（只能说"建议参考XX方向"）
- 替代诊断（不能说"可以不用去医院了"）

---

## 十二、推理轨迹格式

每次 Agent 调用会记录到 `state.agent_call_records`：

```json
{
  "agent": "SyndromeAgent",
  "stage": "syndrome",
  "input_summary": "症状：乏力、气短、自汗...",
  "output_summary": "主证型：脾气虚证 (85%)",
  "llm_calls": 2,
  "rag_chunks_retrieved": 5,
  "duration_ms": 1240,
  "success": true,
  "retry_count": 0,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

前端 `/consult` 页面展示 `agent_steps` 时间线，用户可实时看到各 Agent 的执行状态。

---

## 十三、常见问题

**Q: 后端启动后，前端访问报 404？**
A: 确保前端使用 `npm run dev`（开发）或将 `ui/dist/` 部署到静态服务器。前端开发模式下通过 Vite proxy 代理 `/api` 到 `localhost:8000`。

**Q: 调用 `/api/v2/consult/` 报 500？**
A: 检查 `.env` 中 `LLM_API_KEY` 和 `LLM_API_BASE` 是否正确配置。

**Q: 舌象分析结果不准？**
A: 当前 MVP 版本使用基于颜色统计的规则式提取，建议接入支持视觉输入的模型（如 GPT-4o、Qwen-VL）以获得更准确结果。在 `observation_agent.py` 中替换 `_extract_features_from_image` 方法实现。

**Q: 旧版 `/chat` 页面和新版有什么区别？**
A: 旧版 `/chat` 使用 `/api/chat/` 接口（单一对话，无 Agent 链路）。新版 `/consult` 使用 `/api/v2/consult/` 接口（完整多智能体流程）。两者并存，可通过导航栏切换。

---

*文档版本：v2.0 | 生成时间：2026-03-19 | 项目：Tcm-agent-system*
