# 基于大语言模型的中医智能问诊系统

## 项目简介

欢迎使用**基于大语言模型的中医智能问诊系统**！这是一个结合传统中医理论与现代人工智能技术的创新项目，旨在为用户提供便捷、准确、个性化的中医诊疗服务。

本项目通过先进的向量检索技术和多模态大语言模型，实现症状分析、体质辨识、辨证论治、方剂推荐等中医特色功能，推动中医知识的数字化转型和智能化发展。

---

## 项目背景

随着人工智能技术的快速发展，大语言模型在医疗健康领域的应用日益广泛。然而，中医作为中华文明的瑰宝，其理论体系复杂、辨证论治方法独特，传统中医知识数字化面临诸多挑战：

1. **知识结构化困难**：中医理论体系庞大，包含《黄帝内经》《伤寒论》《金匮要略》等经典著作，以及大量临床案例、方剂、中药等知识，如何将这些非结构化或半结构化的知识转化为机器可理解的形式是一个重大挑战。

2. **语义理解准确度要求高**：中医术语具有独特的语义特征，如"肝阳上亢""气血两虚""痰湿阻肺"等，这些术语在普通语言模型中可能被误解或无法准确理解。

3. **个性化需求强烈**：中医诊疗强调"辨证论治""因人制宜"，不同体质、不同季节、不同地域的患者需要不同的治疗方案，如何实现个性化推荐是关键问题。

4. **知识更新频繁**：中医知识在不断发展和积累，系统需要能够方便地更新和维护知识库，保持知识的时效性和准确性。

5. **多轮对话需求**：中医问诊通常需要多轮对话来收集症状信息、确认诊断、调整方案，如何实现高效的对话管理是重要问题。

---

## 项目目标

本项目的开发目标包括：

1. **理论探索**：探索大语言模型在中医领域的应用模式，研究如何将中医知识与大语言模型结合，为中医智能化提供理论支撑。

2. **实践应用**：构建一个完整的中医智能问诊系统，解决实际应用中的技术难题，为用户提供可用的智能诊疗工具。

3. **技术创新**：采用先进的向量检索技术（pgvector）和混合搜索策略，提升知识检索的准确性和效率，为类似应用提供技术参考。

4. **应用价值**：系统可以辅助中医从业者进行诊断，为普通用户提供中医健康咨询，促进中医知识的传播和应用。

5. **创新价值**：在传统中医与现代AI技术之间架起桥梁，推动中医的数字化转型和智能化发展。

---

## 技术架构

### 总体架构

本系统采用前后端分离的架构设计，整体架构如下：

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                    ┌──────────────┐              ┌──────────────┐
│                    │  前端      │              │  后端      │
│                    │  React + Vite │              │  Django      │
│                    │              │              │              │
│                    └──────────────┘              └──────────────┘
│                                                     │
│                    ┌──────────────┐              ┌──────────────┐
│                    │  向量数据库  │              │  大语言模型   │
│                    │  PostgreSQL   │              │  多模型支持   │
│                    │ + pgvector  │              │              │
│                    └──────────────┘              └──────────────┘
│                                                     │
└─────────────────────────────────────────────────────────────┘
```

### 后端架构

后端采用Django框架，遵循MTV（Model-Template-View）架构模式：

#### 应用模块划分

系统按照功能模块进行划分，主要包含以下应用：

1. **apps.tcm**：核心应用模块
   - 配置管理、URL路由等

2. **apps.knowledge**：知识库管理模块
   - 文档上传、处理、向量化
   - 知识库CRUD操作
   - 向量搜索（相似度搜索）
   - 混合搜索（向量+关键词）

3. **apps.chat**：聊天对话模块
   - 多轮对话管理
   - 会话摘要生成
   - 流式响应处理
   - 知识库检索集成

4. **apps.application**：应用管理模块
   - 应用列表
   - 应用配置
   - 应用统计

5. **apps.model_provider**：模型提供商模块
   - 多模型支持
   - 模型配置管理
   - 统一的模型调用接口

6. **apps.users**：用户管理模块
   - 用户认证
   - 权限管理
   - 用户信息管理

7. **apps.tools**：工具管理模块
   - 工具列表
   - 工具调用

8. **apps.system_manage**：系统管理模块
   - 系统配置
   - 日志管理
   - 数据统计

#### 数据层设计

数据层采用Django ORM，主要模型包括：

1. **KnowledgeBase**：知识库模型
   - 字段：id, name, desc, meta, user_id, is_active
   - 检索相关字段：embedding_model, embedding_dimension, similarity_threshold, search_type, top_k

2. **Document**：文档模型
   - 字段：id, name, file_type, file_size, char_count, paragraph_count, status, progress
   - 关联：knowledge_base（外键）

3. **Paragraph**：段落模型
   - 字段：id, content, title, page_number, meta
   - 关联：document（外键）

4. **Embedding**：向量嵌入模型
   - 字段：id, source_id, source_type, is_active, knowledge, document, paragraph, embedding, search_vector, meta
   - 特殊字段：embedding使用自定义VectorField（vector类型）

5. **ChatMessage**：聊天消息模型
   - 字段：id, session, role, content, create_time
   - 关联：session（外键）

6. **ChatSession**：聊天会话模型
   - 字段：id, application, user, title, summary, create_time, update_time
   - 关联：application, user（外键）

7. **Application**：应用模型
   - 字段：id, name, description, config, is_active, create_time

8. **ModelConfig**：模型配置模型
   - 字段：name, model_type, provider, model_name, credential, params, is_active, is_delete

#### 向量存储设计

系统采用pgvector扩展进行向量存储和检索：

1. **向量表设计**：
   - 表名：tcm_embedding
   - 向量列：embedding（vector(768)类型）
   - 索引：为每个知识库创建独立的ivfflat索引
   - 索引名称：tcm_embedding_idx_{knowledge_base_id}

2. **向量检索策略**：
   - 纯向量搜索：基于余弦相似度
   - 关键词搜索：基于PostgreSQL全文搜索
   - 混合搜索：结合向量和关键词搜索，加权融合结果

3. **向量索引优化**：
   - 使用ivfflat索引类型（适合高维向量）
   - lists参数设置为100（根据向量数量动态调整）
   - WHERE条件过滤：按knowledge_id和document_id过滤

#### API设计

系统采用RESTful API设计，使用Django REST Framework：

1. **认证方式**：Token认证
2. **API版本控制**：使用drf-spectacular自动生成OpenAPI文档
3. **响应格式**：JSON格式
4. **错误处理**：统一的异常处理和错误响应

### 前端架构

前端采用React + Vite技术栈：

1. **技术栈**：
   - React 18
   - TypeScript
   - Vite 5
   - TailwindCSS
   - Ant Design

2. **前端模块划分**：
   - 知识库管理界面
   - 聊天对话界面
   - 应用管理界面
   - 用户管理界面
   - 系统设置界面

3. **状态管理**：使用React Context API或Redux进行状态管理

4. **API集成**：使用axios进行HTTP请求

### 部署架构

系统支持多种部署方式：

1. **本地开发部署**：
   - 使用systemd管理服务
   - Gunicorn作为WSGI服务器
   - Nginx作为反向代理

2. **容器化部署**：
   - Docker Compose
   - 支持PostgreSQL和Django应用

3. **云平台部署**：
   - Fly.io
   - Render
   - Railway

---

## 核心功能

### 知识库管理模块

#### 文档上传与处理

系统支持多种文档格式的上传和处理：

1. **支持的文档格式**：
   - Word文档（.doc, .docx）
   - PDF文档（.pdf）
   - 纯文本文件（.txt）
   - Markdown文件（.md）

2. **文档处理流程**：
   ```
   用户上传文档
   ↓
   文件类型识别
   ↓
   文本提取（使用python-docx、PyPDF2等库）
   ↓
   文本分词和分段
   ↓
   向量化处理（使用SentenceTransformer）
   ↓
   存储到向量数据库（pgvector）
   ↓
   创建向量索引
   ```

3. **关键技术实现**：

**文档提取技术**：
- 使用python-docx库处理Word文档
- 使用PyPDF2库处理PDF文档
- 使用BeautifulSoup4处理HTML文档
- 支持批量文档处理

**文本分段策略**：
- 按段落自动分段（基于换行符）
- 按语义单元分段（基于句子边界）
- 保持段落上下文连贯性
- 控制段落长度（避免过长或过短）

**向量化技术**：
- 使用SentenceTransformer模型（shibing624/text2vec-base-chinese）
- 生成768维向量表示
- 支持本地模型加载
- 支持Hugging Face镜像源配置

**向量索引创建**：
- 使用pgvector的ivfflat索引类型
- 为每个知识库创建独立索引
- 动态调整lists参数（向量数量的平方根）
- 使用余弦相似度操作符（vector_cosine_ops）

**进度跟踪**：
- 实时进度更新（0% → 50% → 100%）
- 支持WebSocket推送进度
- 异常处理和状态回滚

#### 知识库CRUD操作

系统提供完整的知识库管理功能：

1. **知识库操作**：
   - 创建知识库
   - 更新知识库信息
   - 删除知识库
   - 查询知识库列表
   - 知识库详情查询

2. **文档管理**：
   - 上传文档
   - 删除文档
   - 查询文档列表
   - 文档详情查询
   - 文档状态管理（processing, completed, failed, partially_completed）

3. **段落管理**：
   - 查询段落列表
   - 段落详情查询
   - 删除段落

#### 向量搜索功能

系统实现了三种搜索模式：

1. **向量搜索**：
   - 使用余弦相似度计算
   - 支持top-k参数控制返回数量
   - 支持相似度阈值过滤
   - 支持按知识库过滤
   - 支持按文档过滤
   - 支持排除特定段落

2. **关键词搜索**：
   - 使用PostgreSQL全文搜索
   - 基于tsvector字段
   - 支持中文分词
   - 支持多关键词搜索

3. **混合搜索**：
   - 结合向量和关键词搜索结果
   - 加权融合策略（可配置权重）
   - 结果去重和排序
   - 支持自定义融合算法

**向量搜索优化**：
- 预计算查询向量（避免重复计算）
- 使用numpy进行高效向量运算
- 批量查询优化
- 索引命中率统计

### 聊天对话模块

#### 多轮对话管理

系统支持完整的对话管理功能：

1. **会话管理**：
   - 创建新会话
   - 查询会话列表
   - 会话详情查询
   - 删除会话
   - 会话标题管理

2. **消息管理**：
   - 发送用户消息
   - 发送助手消息
   - 查询消息列表
   - 消息详情查询
   - 删除消息

3. **流式响应**：
   - 支持Server-Sent Events（SSE）流式输出
   - 实时流式输出
   - 支持打字机效果
   - 支持中断流式响应

4. **会话摘要**：
   - 自动生成会话摘要
   - 基于对话历史
   - 使用大语言模型生成摘要
   - 支持摘要更新

5. **知识库集成**：
   - 在对话中自动检索相关知识
   - 支持知识库选择
   - 支持搜索模式选择
   - 检索结果自动注入到prompt

#### 对话历史管理

1. **历史记录**：
   - 查询历史会话
   - 查询历史消息
   - 支持分页查询
   - 支持时间范围过滤

2. **上下文管理**：
   - 维护对话上下文（最近N条消息）
   - 支持上下文窗口大小配置
   - 支持上下文压缩策略

### 模型管理模块

#### 多模型支持

系统支持多种大语言模型提供商：

1. **支持的模型提供商**：
   - OpenAI
   - MIMO
   - Anthropic
   - Gemini
   - DeepSeek
   - Kimi
   - Ollama
   - QWen
   - ZhiPu
   - XunFei
   - AlibabaCloud
   - Bedrock
   - AzureOpenAI
   - SiliconFlow
   - TencentCloud
   - VLLM
   - VolcEngine
   - Xorbits

2. **模型配置管理**：
   - 添加模型配置
   - 更新模型配置
   - 删除模型配置
   - 查询模型配置列表
   - 激活/停用模型
   - 配置模型参数

3. **统一调用接口**：
   - 标准化的模型调用接口
   - 支持流式响应
   - 支持参数配置
   - 支持错误重试
   - 支持超时控制

#### 模型切换

系统支持动态模型切换：

1. **应用级模型配置**：
   - 每个应用可以配置默认模型
   - 支持用户自定义模型
   - 支持模型优先级设置

2. **对话级模型切换**：
   - 在对话中切换模型
   - 保持对话上下文
   - 支持模型对比

3. **模型参数管理**：
   - 温度控制
   - 最大token数控制
   - 停止序列控制
   - Top-P控制

### 应用管理模块

#### 应用配置

1. **应用列表**：
   - 查询所有应用
   - 创建新应用
   - 更新应用信息
   - 删除应用

2. **应用设置**：
   - 应用基本信息（名称、描述）
   - 功能开关控制
   - 文件上传配置
   - 模型配置
   - 知识库配置

3. **应用统计**：
   - 用户数量统计
   - 消息数量统计
   - 文档数量统计
   - 知识库使用统计
   - 模型调用统计

### 用户管理模块

#### 用户认证

1. **Token认证**：
   - 基于JWT（JSON Web Token）进行用户认证
   - Token生成和验证机制
   - Token刷新机制
   - Token过期处理

2. **用户信息管理**：
   - 用户基本信息（用户名、邮箱）
   - 用户头像管理
   - 用户偏好设置
   - 用户状态管理

3. **权限管理**：
   - 角色管理（管理员、普通用户）
   - 权限分配
   - 权限验证

### 工具管理模块

#### 工具列表

系统支持工具的注册和管理：

1. **内置工具**：
   - 知识库搜索
   - 文档查询
   - 数据统计

2. **自定义工具**：
   - 支持用户自定义工具
   - 工具参数配置
   - 工具调用权限控制

3. **工具调用**：
   - 同步调用
   - 异步调用
   - 调用结果缓存
   - 错误处理和重试

### 系统管理模块

#### 系统配置

1. **全局配置**：
   - 系统名称
   - 系统描述
   - Logo配置
   - 联系信息

2. **功能开关**：
   - 功能模块开关
   - 功能参数配置
   - 功能状态监控

3. **日志管理**：
   - 日志级别配置
   - 日志文件管理
   - 日志查询和下载
   - 日志轮转和清理

4. **数据统计**：
   - 用户统计
   - 消息统计
   - 文档统计
   - 知识库统计
   - 模型调用统计

---

## 关键技术实现

### 向量检索技术

#### pgvector集成

系统使用pgvector扩展进行向量存储和检索：

1. **向量字段定义**：
   ```python
   class VectorField(models.Field):
       def db_type(self, connection):
           return f'vector({self.dimension})'
   ```

2. **向量索引创建**：
   ```sql
   CREATE INDEX CONCURRENTLY tcm_embedding_idx_{kb_id}
   ON tcm_embedding USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```

3. **向量相似度计算**：
   ```python
   # 计算余弦相似度
   dot_product = np.dot(query_vector, stored_vector)
   query_norm = np.linalg.norm(query_vector)
   stored_norm = np.linalg.norm(stored_vector)
   similarity = dot_product / (query_norm * stored_norm)
   ```

4. **索引优化**：
   - 为每个知识库创建独立索引
   - 动态调整lists参数
   - 使用WHERE条件过滤

#### 混合搜索策略

系统实现了向量搜索和关键词搜索的混合策略：

1. **向量搜索**：
   - 使用pgvector的ivfflat索引
   - 余弦相似度计算
   - 返回top-k个结果

2. **关键词搜索**：
   - 使用PostgreSQL的tsvector字段
   - 全文搜索
   - 中文分词支持

3. **结果融合**：
   ```python
   # 加权融合
   vector_score = vector_results[i]['score'] * 0.7
   keyword_score = keyword_results[i]['score'] * 0.3
   final_score = vector_score + keyword_score
   ```

4. **结果排序**：
   - 按融合分数排序
   - 去重处理
   - 返回最终结果

### 大语言模型集成

#### 模型提供商架构

系统采用插件化的模型提供商架构：

1. **基类设计**：
   ```python
   class BaseLLMProvider:
       def __init__(self, config):
           self.config = config
           
       def chat(self, messages, **kwargs):
           raise NotImplementedError
       
       def stream_chat(self, messages, **kwargs):
           raise NotImplementedError
   ```

2. **具体实现**：
   - OpenAIProvider
   - DeepSeekProvider
   - KimiProvider
   - 等其他提供商

3. **统一接口**：
   ```python
   class GlobalProviderManager:
       def __init__(self):
           self.providers = {}
           self.register_provider('openai', OpenAIProvider)
           self.register_provider('deepseek', DeepSeekProvider)
           # ... 其他提供商
           
       def get_provider(self, provider_key):
           return self.providers.get(provider_key)
           
       def chat(self, provider_key, messages, **kwargs):
           provider = self.get_provider(provider_key)
           return provider.chat(messages, **kwargs)
   ```

4. **配置管理**：
   - 从数据库读取模型配置
   - 支持动态模型切换
   - 参数配置（温度、top_p等）

#### 流式响应处理

系统实现了Server-Sent Events（SSE）流式响应：

1. **SSE实现**：
   ```python
   def stream_response(self, generator):
       response = StreamingHttpResponse(
           content_type='text/event-stream',
       )
       
       for chunk in generator:
           response.write(f'data: {json.dumps(chunk)}\n\n')
           response.flush()
   ```

2. **打字机效果**：
   - 逐字输出
   - 模拟打字机延迟
   - 支持中断控制

3. **错误处理**：
   - 异常捕获和日志记录
   - 优雅降级处理

### 文档处理技术

#### 多格式文档处理

系统支持多种文档格式的处理：

1. **Word文档处理**：
   ```python
   from docx import Document
   
   doc = Document(docx_path)
   paragraphs = []
   for paragraph in doc.paragraphs:
       text = paragraph.text
       paragraphs.append(text)
   ```

2. **PDF文档处理**：
   ```python
   import PyPDF2
   
   pdf_file = open(pdf_path, 'rb')
   pdf_reader = PyPDF2.PdfReader(pdf_file)
   text = ""
   for page in pdf_reader.pages:
       text += page.extract_text()
   ```

3. **文本分段策略**：
   ```python
   def split_text(text, max_length=500):
       sentences = re.split(r'[。！？\n]', text)
       chunks = []
       current_chunk = ""
       for sentence in sentences:
           if len(current_chunk) + len(sentence) <= max_length:
               current_chunk += sentence
           else:
               chunks.append(current_chunk)
               current_chunk = sentence
       return chunks
   ```

4. **进度跟踪**：
   ```python
   class DocumentProcessor:
       def update_progress(self, progress):
           self.document.progress = progress
           self.document.save()
           
       def complete(self):
           self.document.status = 'completed'
           self.document.progress = 100
           self.document.save()
   ```

### 数据库设计

#### 数据模型优化

1. **索引优化**：
   ```sql
   -- 为embedding列创建索引
   CREATE INDEX CONCURRENTLY tcm_embedding_idx_knowledge_id ON tcm_embedding(knowledge_id);
   
   -- 为knowledge_id列创建索引
   CREATE INDEX CONCURRENTLY tcm_embedding_knowledge_id_idx ON tcm_embedding(knowledge_id);
   ```

2. **查询优化**：
   ```python
   -- 使用SELECT只查询需要的字段
   SELECT e.id, e.paragraph_id, e.embedding
   FROM tcm_embedding e
   JOIN tcm_paragraph p ON e.paragraph_id = p.id
   WHERE e.knowledge_id = %s
   LIMIT %s;
   ```

3. **连接池**：
   ```python
   DATABASES = {
       'default': {
           'CONN_MAX_AGE': 600,
           'CONN_HEALTH_CHECKS': True,
           'OPTIONS': {
               'MAX_CONNS': 20,
               'CONN_MAX_AGE': 0,
           }
       }
   }
   ```

### 前端技术

#### React组件设计

系统采用模块化的React组件设计：

1. **知识库组件**：
   - DocumentUpload：文档上传组件
   - KnowledgeBaseList：知识库列表组件
   - DocumentList：文档列表组件
   - VectorSearch：向量搜索组件
   - SearchResults：搜索结果展示组件

2. **聊天组件**：
   - ChatInterface：聊天界面组件
   - MessageList：消息列表组件
   - MessageInput：消息输入组件
   - SessionList：会话列表组件
   - SessionSettings：会话设置组件

3. **应用管理组件**：
   - ApplicationList：应用列表组件
   - ApplicationSettings：应用设置组件
   - StatisticsDashboard：统计仪表板组件

4. **通用组件**：
   - Loading：加载组件
   - ErrorBoundary：错误边界组件
   - Toast：消息提示组件
   - Modal：模态框组件
   - Table：表格组件

#### 状态管理

系统使用React Context API进行状态管理：

1. **全局状态**：
   ```typescript
   interface AppState {
       user: User | null;
       currentSession: Session | null;
       applications: Application[];
       loading: boolean;
   }
   ```

2. **会话状态**：
   ```typescript
   interface SessionState {
       messages: Message[];
       isStreaming: boolean;
       error: Error | null;
       summary: string | null;
   }
   ```

3. **API状态**：
   ```typescript
   interface ApiState {
       isLoading: boolean;
       error: Error | null;
       lastRequestTime: number;
   }
   ```

#### API集成

前端使用axios进行API调用：

1. **API配置**：
   ```typescript
   const api = axios.create({
       baseURL: 'http://127.0.0.1:8000/api',
       timeout: 30000,
       headers: {
           'Content-Type': 'application/json',
           'Authorization': `Bearer ${token}`,
       },
   });
   ```

2. **请求拦截**：
   ```typescript
   api.interceptors.request.use((config) => {
       const token = localStorage.getItem('token');
       if (token) {
           config.headers.Authorization = `Bearer ${token}`;
       }
       return config;
   });
   ```

3. **错误处理**：
   ```typescript
   api.interceptors.response.use((response) => {
       if (response.status === 401) {
           localStorage.removeItem('token');
           window.location.href = '/login';
       }
       return response;
   });
   ```

---

## 项目特色与创新点

### 中医特色功能

#### 智能辨证

系统实现了基于症状分析的智能辨证功能：

1. **症状提取**：
   - 从用户对话中提取症状关键词
   - 使用大语言模型理解症状描述
   - 支持多症状组合分析

2. **体质辨识**：
   - 基于症状和对话历史分析体质
   - 支持九种体质分类（气虚、血虚、阴虚、阳虚、痰湿、湿热等）
   - 提供体质调理建议

3. **辨证论治**：
   - 结合症状、体质、季节等因素进行辨证
   - 提供证型判断（如肝阳上亢、脾胃虚弱等）
   - 给出治则建议

**技术实现**：
```python
def diagnose_symptoms(symptoms, history):
    prompt = f"""
    基于以下症状进行中医辨证分析：
    症状：{symptoms}
    对话历史：{history}
    
    请分析：
    1. 主要证型
    2. 次要证型
    3. 体质判断
    4. 治则建议
    """
    
    response = llm.chat([{
        "role": "system",
        "content": prompt
    }])
    
    return response
```

#### 方剂推荐

系统实现了基于辨证结果的方剂推荐功能：

1. **经典方剂库**：
   - 基于知识库存储经典方剂
   - 包含《伤寒论》《金匮要略》等方剂
   - 支持方剂分类（解表剂、温里剂、补益剂等）

2. **智能推荐**：
   - 基于辨证结果推荐方剂
   - 考虑患者体质
   - 考虑季节因素
   - 考虑地域因素

3. **方剂详情**：
   - 方剂组成
   - 用法用量
   - 煎制方法
   - 注意事项

**技术实现**：
```python
def recommend_prescription(diagnosis, constitution, season):
    prompt = f"""
    基于以下辨证结果推荐方剂：
    证型：{diagnosis}
    体质：{constitution}
    季节：{season}
    
    请推荐：
    1. 主方剂
    2. 辅助方剂
    3. 用法用量
    4. 煎制方法
    5. 注意事项
    """
    
    # 从知识库检索相关方剂
    search_results = vector_store.search(
        query=f"{diagnosis} 方剂",
        k=5,
        filter={'knowledge_id': prescription_kb_id}
    )
    
    response = llm.chat([
        {
            "role": "system",
            "content": f"知识库检索结果：{search_results}\n{prompt}"
        }
    ])
    
    return response
```

#### 个性化建议

系统实现了基于用户体质的个性化建议功能：

1. **体质调理**：
   - 饮食建议
   - 运动建议
   - 生活作息建议
   - 季节养生建议

2. **禁忌提醒**：
   - 基于体质和方剂的禁忌
   - 食物禁忌
   - 药物相互作用提醒

3. **养生方案**：
   - 四季养生方案
   - 日常保健建议
   - 预防保健措施

**技术实现**：
```python
def personalized_recommendation(constitution, diagnosis):
    prompt = f"""
    基于用户体质和辨证结果提供个性化建议：
    体质：{constitution}
    证型：{diagnosis}
    
    请提供：
    1. 饮食调理建议
    2. 运动建议
    3. 生活作息建议
    4. 禁忌提醒
    5. 养生方案
    """
    
    response = llm.chat([{
        "role": "system",
        "content": prompt
    }])
    
    return response
```

### 技术创新点

#### 向量检索优化

1. **动态索引创建**：
   - 为每个知识库自动创建独立索引
   - 根据向量数量动态调整lists参数
   - 使用CONCURRENTLY避免锁表

2. **混合搜索策略**：
   - 向量搜索和关键词搜索的加权融合
   - 可配置的融合权重
   - 结果去重和排序
   - 支持自定义融合算法

3. **查询优化**：
   - 预计算查询向量
   - 批量查询优化
   - 使用numpy进行高效向量运算
   - 索引命中率统计

#### 多模型管理

1. **统一模型接口**：
   - 标准化的模型调用接口
   - 支持多种模型无缝切换
   - 动态模型切换

2. **模型参数管理**：
   - 温度、top_p、max_tokens等参数配置
   - 支持应用级和对话级配置

3. **模型性能监控**：
   - 模型调用次数统计
   - 响应时间监控
   - 错误率统计

#### 流式响应优化

1. **SSE优化**：
   - 使用Server-Sent Events实现流式响应
   - 支持打字机效果
   - 优化数据传输

2. **WebSocket优化**：
   - 实时双向通信
   - 心跳机制
   - 断线重连

#### 文档处理优化

1. **批量处理**：
   - 支持批量文档上传
   - 并行文档处理
   - 异步任务队列

2. **进度跟踪**：
   - 实时进度更新
   - WebSocket推送
   - 异常状态处理

3. **错误恢复**：
   - 失败文档重试机制
   - 部分处理状态保留
   - 错误日志记录

---

## 系统设计

### 安全设计

#### 认证与授权

1. **Token认证**：
   - 基于JWT（JSON Web Token）进行用户认证
   - Token生成和验证机制
   - Token刷新和过期处理

2. **权限控制**：
   - 基于角色的权限管理
   - 用户、管理员、超级管理员
   - 资源访问控制

3. **数据安全**：
   - 敏感数据加密存储
   - SQL注入防护
   - XSS防护
   - CSRF防护

**技术实现**：
```python
# JWT认证
from rest_framework_simplejwt.tokens import RefreshToken

class TokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        user = authenticate(
            username=request.data['username'],
            password=request.data['password'],
        )
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh.access_token),
            'access': str(refresh.access_token),
        })

# 权限控制
class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view, obj):
        return request.user.is_staff
```

#### 数据安全

1. **输入验证**：
   - 所有用户输入进行验证和清理
   - 文件上传类型验证
   - SQL注入防护

2. **输出编码**：
   - JSON响应统一编码
   - 敏感信息脱敏
   - 错误信息统一格式

3. **日志审计**：
   - 关键操作日志记录
   - 异常日志记录
   - 访问日志记录

### 性能设计

#### 数据库性能

1. **索引优化**：
   - 为常用查询字段创建索引
   - 使用合适的索引类型（B-tree、Hash、GiST）
   - 定期分析和优化慢查询

2. **查询优化**：
   - 使用SELECT只查询需要的字段
   - 使用LIMIT限制返回数量
   - 避免N+1查询问题

3. **连接池**：
   - 配置合理的连接池大小
   - 设置连接超时时间
   - 启用连接健康检查

4. **缓存策略**：
   - 使用Redis缓存热点数据
   - 缓存查询结果
   - 缓存用户信息

#### 应用性能

1. **静态文件优化**：
   - 使用CDN托管静态文件
   - 启用Gzip压缩
   - 设置合理的缓存策略

2. **API性能**：
   - 使用异步处理
   - 批量操作优化
   - 响应压缩

3. **前端性能**：
   - 组件懒加载
   - 虚拟滚动优化
   - 图片懒加载

### 可扩展性设计

#### 模块化设计

1. **功能模块独立**：
   - 每个功能模块独立开发和部署
   - 模块间通过API通信
   - 支持模块独立升级

2. **插件化架构**：
   - 模型提供商插件化
   - 工具插件化
   - 搜索策略插件化

3. **配置化设计**：
   - 功能开关配置
   - 参数配置化
   - 多环境配置支持

#### 数据库设计

1. **多数据库支持**：
   - 当前支持PostgreSQL
   - 设计支持MySQL、MongoDB等
   - 数据库切换配置

2. **分库分表**：
   - 支持按业务模块分库
   - 支持大数据量表分区

3. **数据迁移**：
   - Django ORM迁移机制
   - 支持数据迁移和回滚
   - 迁移版本管理

---

## 部署方案

### 本地开发部署

#### systemd管理（推荐）

使用systemd管理服务：

1. **创建systemd服务文件**：
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
   ```

2. **启动服务**：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable tcm-agent
   sudo systemctl start tcm-agent
   ```

3. **配置Nginx**：
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

### Docker Compose部署

使用Docker Compose进行容器化部署：

1. **docker-compose.yml**：
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

### 云平台部署

#### Fly.io部署

免费额度：
- 每月免费额度：3 GB内存 × 24小时 × 30天
- 数据库：1 GB共享PostgreSQL
- 带宽：160 GB/月
- 请求次数：100,000次/月

#### Render部署

支持多种数据库和自动SSL证书

#### Railway部署

简单易用的容器化部署平台

---

## 项目亮点

### 用户体验

- 流式响应提供实时反馈
- 打字机效果增强交互体验
- 进度跟踪让用户了解处理状态
- 多轮对话支持复杂的问诊场景

### 开发者友好

- 清晰的代码结构和注释
- 完善的API文档（使用drf-spectacular）
- 详细的部署指南
- 丰富的测试用例

### 运维友好

- systemd服务管理
- Docker容器化部署
- 完善的日志和监控
- 自动化的备份策略

### 技术先进性

- 采用pgvector进行向量存储和检索
- 使用SentenceTransformer进行文本向量化
- 支持多种大语言模型提供商
- 实现流式响应（SSE）
- 混合搜索策略（向量+关键词）
- 动态索引创建和优化

### 中医特色

- 智能辨证功能
- 方剂推荐功能
- 个性化建议功能
- 体质辨识功能
- 禁忌提醒功能

### 系统可靠性

- 完善的错误处理机制
- 进度跟踪和状态管理
- 日志记录和审计
- 数据备份策略
- 安全防护措施

---

## 快速开始

### 环境准备

1. **Python环境**：
   ```bash
   python3 --version
   ```

2. **Node.js环境**：
   ```bash
   node --version
   ```

3. **PostgreSQL**：
   ```bash
   psql --version
   ```

### 本地运行

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境
cp .env.example .env
nano .env  # 编辑配置

# 4. 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 5. 创建超级用户（首次部署）
python manage.py createsuperuser

# 6. 使用systemd启动（参考部署指南）
sudo systemctl daemon-reload
sudo systemctl enable tcm-agent
sudo systemctl start tcm-agent
```

---

## 技术栈

- **后端**：Django 5.2.9, Python 3.11
- **前端**：React 18, Vite 5
- **数据库**：PostgreSQL 16, pgvector
- **向量模型**：SentenceTransformer
- **部署**：systemd, Docker Compose

---

## 联系与支持

如有任何问题或建议，欢迎通过以下方式联系：

- **GitHub Issues**：提交问题和建议
- **技术文档**：查阅项目文档
- **社区支持**：参与技术讨论

---

**项目信息**

- **项目名称**：基于大语言模型的中医智能问诊系统
- **开发语言**：Python 3.11
- **后端框架**：Django 5.2.9
- **前端框架**：React 18 + Vite 5
- **数据库**：PostgreSQL 16 + pgvector
- **向量模型**：SentenceTransformer
- **开发周期**：2025年1月 - 2026年1月

---

**最后更新**：2026年1月19日

欢迎使用这个基于大语言模型的中医智能问诊系统！
