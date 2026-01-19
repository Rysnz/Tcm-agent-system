import request from '@/utils/request'

export interface KnowledgeBase {
  id: string
  name: string
  desc: string
  meta: Record<string, any>
  user_id: string
  is_active: boolean
  create_time: string
  update_time: string
  // 检索相关设置
  embedding_model: string
  embedding_dimension: number
  similarity_threshold: number
  search_type: 'embedding' | 'keywords' | 'blend'
  top_k: number
}

export interface Document {
  id: string
  knowledge_base: string
  name: string
  file_type: string
  file_size: number
  file_path: string
  char_count: number
  paragraph_count: number
  status: string
  progress: number
  meta: Record<string, any>
}

export interface Application {
  id: string
  name: string
  desc: string
  icon: string
  user_id: string
  work_flow: Record<string, any>
  model_config: {
    greeting?: string
    output_thinking?: boolean
    voice_input?: boolean
    voice_output?: boolean
    tts_type?: string
    stt_model?: string
    tts_model?: string
    history_count?: number
    prompt_without_knowledge?: string
    prompt_with_knowledge?: string
  }
  knowledge_bases: string | string[]
  tools: string[]
  prompt_template: string
  system_prompt: string
  prompt_template_type: string
  similarity_threshold: number
  top_k?: number
  enable_file_upload?: boolean
  is_active: boolean
}

export interface ChatSession {
  id: string
  application_id: string
  user_id: string
  session_name: string
  meta: Record<string, any>
  create_time: string
}

export interface ChatMessage {
  id: string
  session: string
  role: string
  content: string
  message_type: string
  meta: Record<string, any>
  create_time: string
}

export const knowledgeApi = {
  getKnowledgeBases: async () => {
    try {
      const response = await request.get<PaginatedResponse<KnowledgeBase>>('/knowledge/knowledge_base/')
      return response.results || []
    } catch (error) {
      console.error('获取知识库列表失败:', error)
      return []
    }
  },
  
  getKnowledgeBase: async (id: string) => {
    try {
      const response = await request.get<KnowledgeBase>(`/knowledge/knowledge_base/${id}/`)
      return response
    } catch (error) {
      console.error('获取知识库详情失败:', error)
      throw error
    }
  },
  
  createKnowledgeBase: (data: Partial<KnowledgeBase>) => 
    request.post('/knowledge/knowledge_base/', data),
  
  updateKnowledgeBase: (id: string, data: Partial<KnowledgeBase>) => 
    request.put(`/knowledge/knowledge_base/${id}/`, data),
  
  deleteKnowledgeBase: (id: string) => 
    request.delete(`/knowledge/knowledge_base/${id}/`),
  
  getDocuments: async (knowledgeBaseId: string) => {
    try {
      const response = await request.get<PaginatedResponse<Document>>(`/knowledge/document/?knowledge_base=${knowledgeBaseId}`)
      return response.results || []
    } catch (error) {
      console.error('获取文档列表失败:', error)
      return []
    }
  },
  
  uploadDocument: (formData: FormData) => 
    request.post('/knowledge/upload/', formData), // 移除手动设置的Content-Type，让浏览器自动处理
  
  deleteDocument: (documentId: string) => 
    request.delete(`/knowledge/document/${documentId}/`),
  
  searchKnowledge: (data: { knowledge_base_id: string; query: string; top_k?: number }) => 
    request.post('/knowledge/search/', data)
}

interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export const applicationApi = {
  getApplications: async () => {
    const response = await request.get<{count: number; next: string | null; previous: string | null; results: any[]}>('/application/')
    // 解析返回结果中的JSON字段
    return response.results.map(app => {
      let parsedModelConfig = {};
      let parsedWorkFlow = {};
      let parsedTools: string[] = [];
      let parsedKnowledgeBases: string[] = [];
      
      // 解析model_config
      try {
        if (typeof app.model_config === 'string') {
          parsedModelConfig = JSON.parse(app.model_config);
        } else if (typeof app.model_config === 'object' && app.model_config !== null) {
          parsedModelConfig = app.model_config;
        } else {
          parsedModelConfig = {};
        }
      } catch (error) {
        console.error('解析model_config失败:', error);
        parsedModelConfig = {};
      }
      
      // 解析work_flow
      try {
        if (typeof app.work_flow === 'string') {
          parsedWorkFlow = JSON.parse(app.work_flow);
        } else if (typeof app.work_flow === 'object' && app.work_flow !== null) {
          parsedWorkFlow = app.work_flow;
        } else {
          parsedWorkFlow = {};
        }
      } catch (error) {
        console.error('解析work_flow失败:', error);
        parsedWorkFlow = {};
      }
      
      // 解析tools
      try {
        if (typeof app.tools === 'string') {
          parsedTools = JSON.parse(app.tools);
        } else if (Array.isArray(app.tools)) {
          parsedTools = app.tools;
        } else {
          parsedTools = [];
        }
      } catch (error) {
        console.error('解析tools失败:', error);
        parsedTools = [];
      }
      
      // 解析knowledge_bases
      try {
        if (typeof app.knowledge_bases === 'string') {
          parsedKnowledgeBases = JSON.parse(app.knowledge_bases);
        } else if (Array.isArray(app.knowledge_bases)) {
          parsedKnowledgeBases = app.knowledge_bases;
        } else {
          parsedKnowledgeBases = [];
        }
      } catch (error) {
        console.error('解析knowledge_bases失败:', error);
        parsedKnowledgeBases = [];
      }
      
      // 确保返回的对象符合Application类型
      const result = {
        ...app,
        model_config: parsedModelConfig,
        work_flow: parsedWorkFlow,
        tools: parsedTools,
        knowledge_bases: parsedKnowledgeBases
      };
      
      // 添加缺少的必要字段
      if (!result.top_k) {
        result.top_k = parsedModelConfig.top_k || 5;
      }
      
      return result as Application;
    })
  },
  
  createApplication: (data: Partial<Application>) => {
    // 处理JSON对象字段，转换为字符串
    const processedData = {
      ...data,
      model_config: typeof data.model_config === 'object' ? JSON.stringify(data.model_config) : data.model_config,
      work_flow: typeof data.work_flow === 'object' ? JSON.stringify(data.work_flow) : data.work_flow,
      tools: Array.isArray(data.tools) ? JSON.stringify(data.tools) : data.tools,
      knowledge_bases: Array.isArray(data.knowledge_bases) ? JSON.stringify(data.knowledge_bases) : data.knowledge_bases
    };
    return request.post('/application/', processedData);
  },
  
  updateApplication: (id: string, data: Partial<Application>) => {
    // 处理JSON对象字段，转换为字符串
    const processedData = {
      ...data,
      model_config: typeof data.model_config === 'object' ? JSON.stringify(data.model_config) : data.model_config,
      work_flow: typeof data.work_flow === 'object' ? JSON.stringify(data.work_flow) : data.work_flow,
      tools: Array.isArray(data.tools) ? JSON.stringify(data.tools) : data.tools,
      knowledge_bases: Array.isArray(data.knowledge_bases) ? JSON.stringify(data.knowledge_bases) : data.knowledge_bases
    };
    return request.put(`/application/${id}/`, processedData);
  },
  
  deleteApplication: (id: string) => 
    request.delete(`/application/${id}/`),
  
  executeWorkflow: (data: { application_id: string; input_data: Record<string, any> }) => 
    request.post('/application/workflow/execute/', data),
  
  validateWorkflow: (data: { application_id: string }) => 
    request.post('/application/workflow/validate/', data),
  
  saveWorkflow: (data: { application_id: string; nodes: any[]; edges: any[] }) => 
    request.post('/application/workflow/save/', data),
  
  // 获取应用统计数据
  getStats: (params: { timeRange?: string; startDate?: string; endDate?: string }) => 
    request.get<StatsResponse>('/application/stats/', params)
}

export const chatApi = {
  getSessions: async (applicationId: string) => {
    const response = await request.get<PaginatedResponse<ChatSession>>(`/chat/session/?application_id=${applicationId}`)
    return response.results
  },
  
  createSession: (data: Partial<ChatSession>) => 
    request.post('/chat/session/', data),
    
  deleteSession: (sessionId: string) => 
    request.delete(`/chat/session/${sessionId}/delete_session/`),
  
  getMessages: async (sessionId: string) => {
    const response = await request.get<PaginatedResponse<ChatMessage>>(`/chat/message/?session_id=${sessionId}`)
    return response.results
  },
  
  sendMessage: (data: { application_id: string; message: string; session_id?: string }) => 
    request.post('/chat/', data),
    
  sendStreamMessage: (data: { application_id: string; message: string; session_id?: string }) => 
    request.post('/chat/stream/', data, { responseType: 'stream' }),
    
  // 语音转文字API
  speechToText: async (file: Blob, applicationId: string = 'default') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('application_id', applicationId)
    const response = await request.post('/chat/speech_to_text/', formData)
    return response
  },
  
  // 文件上传API
  uploadFile: async (formData: FormData) => {
    const response = await request.post('/chat/upload_file/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response
  }
}

export const toolsApi = {
  getTools: async () => {
    try {
      const response = await request.get<PaginatedResponse<any>>('/tools/tool/')
      return response.results || []
    } catch (error) {
      console.error('获取工具列表失败:', error)
      return []
    }
  },
  
  createTool: (data: any) => 
    request.post('/tools/tool/', data),
  
  callTool: (data: { tool_name: string; params: Record<string, any> }) => 
    request.post('/tools/call/', data)
}

// 模型配置类型定义
export interface ModelConfig {
  id: string;
  name: string;
  provider: string;
  model_type: string;
  model_name: string;
  credential: any;
  is_active: boolean;
  create_time?: string;
  update_time?: string;
}

// 提供商信息类型
export interface ProviderInfo {
  provider: string;
  name: string;
  icon: string;
}

// 模型类型信息
export interface ModelType {
  value: string;
  label: string;
}

// 模型列表项
export interface ModelListItem {
  value: string;
  label: string;
}

// 统计数据类型定义
export interface StatsData {
  userCount: number;
  questionCount: number;
  tokensCount: number;
  satisfactionRate: number;
}

// 图表数据类型定义
export interface ChartItem {
  name: string;
  values: number[];
  dates: string[];
  color: string;
  icon: string;
}

// 统计响应类型
export interface StatsResponse {
  stats: StatsData;
  charts: ChartItem[];
}

// 参数表单配置
export interface ParamFormConfig {
  key: string;
  label: string;
  type: 'text' | 'number' | 'slider' | 'select' | 'boolean';
  value: any;
  min?: number;
  max?: number;
  step?: number;
  options?: Array<{label: string; value: any}>;
  placeholder?: string;
  helpText?: string;
  formatTooltip?: (val: any) => string;
}

// 模型管理API
export const modelApi = {
  // 获取模型列表
  getModels: async () => {
    try {
      const response = await request.get<PaginatedResponse<ModelConfig>>('/model/model-config/')
      return response.results
    } catch (error) {
      console.error('获取模型列表失败:', error)
      return []
    }
  },
  
  // 获取提供商列表
  getProviders: async () => {
    try {
      return await request.get<ProviderInfo[]>('/model/providers/')
    } catch (error) {
      console.error('获取提供商列表失败:', error)
      return []
    }
  },
  
  // 获取模型类型列表
  getModelTypes: async () => {
    try {
      return await request.get<ModelType[]>('/model/model-types/')
    } catch (error) {
      console.error('获取模型类型列表失败:', error)
      return []
    }
  },
  
  // 获取模型列表
  getModelList: async (provider: string, modelType: string) => {
    try {
      return await request.get<ModelListItem[]>(`/model/model-list/?provider=${provider}&model_type=${modelType}`)
    } catch (error) {
      console.error('获取模型列表失败:', error)
      return []
    }
  },
  
  // 验证模型凭证
  validateCredential: async (provider: string, modelType: string, modelName: string, credential: any) => {
    try {
      return await request.post('/model/validate-credential/', {
        provider,
        model_type: modelType,
        model_name: modelName,
        credential
      })
    } catch (error) {
      console.error('验证模型凭证失败:', error)
      return { is_valid: false }
    }
  },
  
  // 获取模型参数表单
  getModelParamsForm: async (provider: string, modelName: string) => {
    try {
      return await request.get<ParamFormConfig[]>(`/model/model-params-form/?provider=${provider}&model_name=${modelName}`)
    } catch (error) {
      console.error('获取模型参数表单失败:', error)
      return []
    }
  },
  
  // 创建模型
  createModel: async (data: Partial<ModelConfig>) => {
    try {
      return await request.post('/model/model-config/', data)
    } catch (error) {
      console.error('创建模型失败:', error)
      throw error
    }
  },
  
  // 更新模型
  updateModel: async (data: ModelConfig) => {
    try {
      return await request.put(`/model/model-config/${data.id}/`, data)
    } catch (error) {
      console.error('更新模型失败:', error)
      throw error
    }
  },
  
  // 删除模型
  deleteModel: async (id: string) => {
    try {
      return await request.delete(`/model/model-config/${id}/`)
    } catch (error) {
      console.error('删除模型失败:', error)
      throw error
    }
  }
}
