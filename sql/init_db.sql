-- 启用pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建知识库表
CREATE TABLE IF NOT EXISTS tcm_knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    desc TEXT,
    meta JSONB,
    user_id UUID NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete BOOLEAN DEFAULT FALSE
);

-- 创建文档表
CREATE TABLE IF NOT EXISTS tcm_document (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID NOT NULL REFERENCES tcm_knowledge_base(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    file_type VARCHAR(32) NOT NULL,
    file_size BIGINT NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    char_count INTEGER DEFAULT 0,
    paragraph_count INTEGER DEFAULT 0,
    status VARCHAR(32) DEFAULT 'processing',
    meta JSONB,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete BOOLEAN DEFAULT FALSE
);

-- 创建段落表
CREATE TABLE IF NOT EXISTS tcm_paragraph (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES tcm_document(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    title VARCHAR(255),
    page_number INTEGER,
    meta JSONB,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete BOOLEAN DEFAULT FALSE
);

-- 创建向量存储表
CREATE TABLE IF NOT EXISTS tcm_vector_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    knowledge_base_id UUID NOT NULL REFERENCES tcm_knowledge_base(id) ON DELETE CASCADE,
    paragraph_id UUID NOT NULL REFERENCES tcm_paragraph(id) ON DELETE CASCADE,
    vector JSONB NOT NULL,
    embedding_model VARCHAR(128) NOT NULL,
    dimension INTEGER NOT NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete BOOLEAN DEFAULT FALSE
);

-- 创建应用表
CREATE TABLE IF NOT EXISTS tcm_application (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    desc TEXT,
    icon VARCHAR(512),
    user_id UUID NOT NULL,
    work_flow JSONB DEFAULT '{}',
    model_config JSONB DEFAULT '{}',
    knowledge_bases JSONB DEFAULT '[]',
    tools JSONB DEFAULT '[]',
    prompt_template TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete BOOLEAN DEFAULT FALSE
);

-- 创建工作流节点表
CREATE TABLE IF NOT EXISTS tcm_workflow_node (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES tcm_application(id) ON DELETE CASCADE,
    node_id VARCHAR(64) NOT NULL,
    node_type VARCHAR(32) NOT NULL,
    node_data JSONB DEFAULT '{}',
    position JSONB DEFAULT '{}',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete BOOLEAN DEFAULT FALSE
);

-- 创建工作流边表
CREATE TABLE IF NOT EXISTS tcm_workflow_edge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES tcm_application(id) ON DELETE CASCADE,
    source_node VARCHAR(64) NOT NULL,
    target_node VARCHAR(64) NOT NULL,
    edge_data JSONB DEFAULT '{}',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete BOOLEAN DEFAULT FALSE
);

-- 创建聊天会话表
CREATE TABLE IF NOT EXISTS tcm_chat_session (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES tcm_application(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    session_name VARCHAR(128) NOT NULL,
    meta JSONB,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete BOOLEAN DEFAULT FALSE
);

-- 创建聊天消息表
CREATE TABLE IF NOT EXISTS tcm_chat_message (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES tcm_chat_session(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(32) DEFAULT 'text',
    meta JSONB,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete BOOLEAN DEFAULT FALSE
);

-- 创建工具表
CREATE TABLE IF NOT EXISTS tcm_tool (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(128) NOT NULL,
    desc TEXT,
    tool_type VARCHAR(32) NOT NULL,
    tool_config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete BOOLEAN DEFAULT FALSE
);

-- 创建MCP工具表
CREATE TABLE IF NOT EXISTS tcm_mcp_tool (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_id UUID NOT NULL REFERENCES tcm_tool(id) ON DELETE CASCADE,
    mcp_server_url VARCHAR(512) NOT NULL,
    mcp_config JSONB DEFAULT '{}',
    tool_schema JSONB DEFAULT '{}',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_delete BOOLEAN DEFAULT FALSE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_tcm_knowledge_base_user_id ON tcm_knowledge_base(user_id);
CREATE INDEX IF NOT EXISTS idx_tcm_knowledge_base_is_delete ON tcm_knowledge_base(is_delete);
CREATE INDEX IF NOT EXISTS idx_tcm_document_knowledge_base ON tcm_document(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_tcm_document_is_delete ON tcm_document(is_delete);
CREATE INDEX IF NOT EXISTS idx_tcm_vector_store_knowledge_base ON tcm_vector_store(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_tcm_vector_store_is_delete ON tcm_vector_store(is_delete);
CREATE INDEX IF NOT EXISTS idx_tcm_application_user_id ON tcm_application(user_id);
CREATE INDEX IF NOT EXISTS idx_tcm_application_is_delete ON tcm_application(is_delete);
CREATE INDEX IF NOT EXISTS idx_tcm_workflow_node_application ON tcm_workflow_node(application_id);
CREATE INDEX IF NOT EXISTS idx_tcm_workflow_node_is_delete ON tcm_workflow_node(is_delete);
CREATE INDEX IF NOT EXISTS idx_tcm_workflow_edge_application ON tcm_workflow_edge(application_id);
CREATE INDEX IF NOT EXISTS idx_tcm_workflow_edge_is_delete ON tcm_workflow_edge(is_delete);
CREATE INDEX IF NOT EXISTS idx_tcm_chat_session_application ON tcm_chat_session(application_id);
CREATE INDEX IF NOT EXISTS idx_tcm_chat_session_is_delete ON tcm_chat_session(is_delete);
CREATE INDEX IF NOT EXISTS idx_tcm_chat_message_session ON tcm_chat_message(session_id);
CREATE INDEX IF NOT EXISTS idx_tcm_chat_message_is_delete ON tcm_chat_message(is_delete);
CREATE INDEX IF NOT EXISTS idx_tcm_tool_is_delete ON tcm_tool(is_delete);
CREATE INDEX IF NOT EXISTS idx_tcm_mcp_tool_tool ON tcm_mcp_tool(tool_id);
CREATE INDEX IF NOT EXISTS idx_tcm_mcp_tool_is_delete ON tcm_mcp_tool(is_delete);
