import uuid
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import StreamingHttpResponse
import json
import os
from apps.chat.models import ChatSession, ChatMessage
from apps.chat.serializers import ChatSessionSerializer, ChatMessageSerializer
from apps.application.flow.workflow_manage import TCMWorkflowManager
from apps.model_provider.provider_manager import global_provider_manager
from apps.model_provider.base_model_provider import ModelTypeConst
from pydub import AudioSegment
import tempfile

class ChatSessionViewSet(viewsets.ModelViewSet):
    queryset = ChatSession.objects.filter(is_delete=False)
    serializer_class = ChatSessionSerializer
    
    def get_queryset(self):
        # 确保所有查询包含is_delete=False过滤条件
        queryset = ChatSession.objects.filter(is_delete=False)
        
        # 处理application_id查询参数
        application_id = self.request.query_params.get('application_id')
        if application_id:
            # 处理默认应用ID
            if application_id == 'default':
                from apps.application.models import Application
                try:
                    # 获取第一个激活的应用，按创建时间排序
                    default_app = Application.objects.filter(is_delete=False, is_active=True).order_by('create_time').first()
                    if default_app:
                        application_id = str(default_app.id)
                    else:
                        # 如果没有默认应用，使用固定UUID
                        application_id = str(uuid.uuid5(uuid.NAMESPACE_OID, 'default-application'))
                except Exception as e:
                    # 失败时使用固定UUID作为备选方案
                    application_id = str(uuid.uuid5(uuid.NAMESPACE_OID, 'default-application'))
            
            queryset = queryset.filter(application_id=application_id)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        # 处理默认应用ID
        if request.data.get('application_id') == 'default':
            from apps.application.models import Application
            try:
                user_id = self.request.user.id if hasattr(self.request.user, 'id') and self.request.user.id else str(uuid.uuid4())
                # 获取第一个激活的应用，按创建时间排序
                default_app = Application.objects.filter(is_delete=False, is_active=True).order_by('create_time').first()
                if default_app:
                    request.data['application_id'] = str(default_app.id)
                else:
                    # 如果没有默认应用，创建一个
                    application_id = str(uuid.uuid5(uuid.NAMESPACE_OID, 'default-application'))
                    default_app, created = Application.objects.get_or_create(
                        id=application_id,
                        defaults={
                            'name': '默认应用',
                            'desc': '系统默认应用',
                            'user_id': user_id,
                            'is_active': True
                        }
                    )
                    request.data['application_id'] = application_id
            except Exception as e:
                # 失败时使用固定UUID作为备选方案
                request.data['application_id'] = str(uuid.uuid5(uuid.NAMESPACE_OID, 'default-application'))
        
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        # 处理用户ID，未认证时生成临时UUID
        user_id = self.request.user.id if hasattr(self.request.user, 'id') and self.request.user.id else str(uuid.uuid4())
        serializer.save(user_id=user_id)
    
    @action(detail=True, methods=['delete'])
    def delete_session(self, request, pk=None):
        """删除会话"""
        try:
            session = self.get_object()
            session.is_delete = True
            session.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ChatMessageViewSet(viewsets.ModelViewSet):
    queryset = ChatMessage.objects.filter(is_delete=False)
    serializer_class = ChatMessageSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        return queryset

class ChatView(APIView):
    
    def post(self, request):
        application_id = request.data.get('application_id')
        user_message = request.data.get('message', '')
        session_id = request.data.get('session_id')
        
        # 检查应用是否启用文件上传功能
        enable_file_upload = True
        try:
            from apps.application.models import Application
            application = Application.objects.get(id=application_id)
            enable_file_upload = getattr(application, 'enable_file_upload', True)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"获取应用文件上传设置失败: {str(e)}，默认启用文件上传")
        
        # 处理文件上传
        file_list = []
        
        # 只有在启用文件上传时才处理文件
        if enable_file_upload:
            # 处理通过multipart/form-data上传的文件
            uploaded_files = request.FILES.getlist('files', [])
            for file in uploaded_files:
                try:
                    from apps.chat.serializers import FileUploadSerializer
                    serializer = FileUploadSerializer(data={
                        'file': file,
                        'source_id': session_id or FileSourceType.CHAT.value,
                        'source_type': FileSourceType.CHAT.value
                    })
                    if serializer.is_valid():
                        result = serializer.upload()
                        file_list.append({
                            'file_id': result['file_id'],
                            'file_name': result['file_name'],
                            'file_size': result['file_size'],
                            'url': result['url']
                        })
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"文件上传失败: {str(e)}")
            
            # 处理通过JSON格式发送的文件信息
            json_files = request.data.get('files', [])
            if isinstance(json_files, list):
                file_list.extend(json_files)
        
        # 如果没有消息但有文件，使用默认消息
        if not user_message and file_list:
            user_message = '请分析上传的文件'
        
        if not user_message:
            return Response(
                {'error': 'message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 处理用户ID，未认证时生成临时UUID
        user_id = request.user.id if hasattr(request.user, 'id') and request.user.id else uuid.uuid4()
        
        # 检查是否使用默认应用ID
        is_default_app = application_id == 'default'
        
        # 处理application_id，对于默认应用，使用固定的UUID或获取第一个激活的应用
        if is_default_app:
            # 导入必要的模块
            import logging
            logger = logging.getLogger(__name__)
            from apps.application.models import Application
            try:
                # 获取第一个激活的应用，按创建时间排序
                default_app = Application.objects.filter(is_delete=False, is_active=True).order_by('create_time').first()
                if default_app:
                    # 使用现有的默认应用
                    application_id = str(default_app.id)
                    logger.info(f"使用现有默认应用: {application_id}, 名称: {default_app.name}")
                else:
                    # 如果没有现有应用，创建一个默认应用
                    logger.info(f"创建新的默认应用")
                    # 生成固定UUID，确保每次使用默认应用时保持一致
                    application_id = str(uuid.uuid5(uuid.NAMESPACE_OID, 'default-application'))
                    # 检查应用是否已存在
                    default_app, created = Application.objects.get_or_create(
                        id=application_id,
                        defaults={
                            'name': '默认应用',
                            'desc': '系统默认应用',
                            'user_id': user_id,
                            'is_active': True
                        }
                    )
                    logger.info(f"{'创建' if created else '使用'}默认应用: {application_id}, 名称: {default_app.name}")
            except Exception as e:
                logger.error(f"处理默认应用失败: {e}")
                # 失败时使用临时UUID作为备选方案
                application_id = str(uuid.uuid4())
        
        try:
            if not session_id:
                session = ChatSession.objects.create(
                    application_id=application_id,
                    user_id=user_id,
                    session_name='新建对话'
                )
                session_id = str(session.id)
            else:
                # 处理UUID转换，将"default"转换为有效UUID
                try:
                    session = ChatSession.objects.get(id=session_id, is_delete=False)
                except (ChatSession.DoesNotExist, ValueError):
                    # 如果session_id无效或不存在，创建新会话
                    logger.info(f"Invalid or non-existent session_id: {session_id}, creating new session")
                    session = ChatSession.objects.create(
                        application_id=application_id,
                        user_id=user_id,
                        session_name='新建对话'
                    )
                    session_id = str(session.id)
        except Exception as e:
            # 如果session_id无效或不存在，创建新会话
            logger.info(f"Invalid or non-existent session_id: {session_id}, creating new session")
            session = ChatSession.objects.create(
                application_id=application_id,
                user_id=user_id,
                session_name='新建对话'
            )
            session_id = str(session.id)
        
        user_tokens = len(user_message) // 4
        ChatMessage.objects.create(
            session_id=session_id,
            role='user',
            content=user_message,
            files=file_list if file_list else None,
            tokens=user_tokens
        )
        
        try:
            # 添加日志，调试_is_medical_query方法
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"User message: {user_message}")
            
            # 判断是否是问诊相关内容
            is_medical_query = self._is_medical_query(user_message)
            logger.info(f"Is medical query: {is_medical_query}")
            
            try:
                if is_medical_query and not is_default_app:
                    # 问诊相关内容且不是默认应用，尝试执行完整的工作流
                    logger.info("Executing full workflow for medical query")
                    workflow_manager = TCMWorkflowManager(application_id)
                    result = workflow_manager.execute_diagnosis_workflow([user_message])
                    
                    assistant_message = result.get('context', {}).get('final_response', '')
            except Exception as workflow_error:
                # 工作流执行失败，直接调用大模型生成回复
                logger.error(f"Workflow execution failed: {workflow_error}")
                is_medical_query = False
            
            if not is_medical_query or is_default_app:
                # 普通对话或工作流执行失败或默认应用，先检索知识库内容，再调用大模型
                logger.info("Executing direct LLM call with knowledge base retrieval")
                from langchain_openai import ChatOpenAI
                import os
                
                # 检索知识库内容
                knowledge_context = ""
                top_results = []
                try:
                    from apps.application.models import Application
                    from apps.knowledge.vector.pg_vector import PGVectorStore
                    
                    # 获取应用关联的知识库
                    application = Application.objects.get(id=application_id)
                    
                    # 解析知识库字段（处理可能的JSON字符串）
                    knowledge_base_ids = application.knowledge_bases
                    if isinstance(knowledge_base_ids, str):
                        import json
                        knowledge_base_ids = json.loads(knowledge_base_ids)
                    elif not isinstance(knowledge_base_ids, list):
                        knowledge_base_ids = []
                    
                    logger.info(f"应用关联的知识库: {knowledge_base_ids}")
                    
                    # 如果有关联的知识库，进行检索
                    if knowledge_base_ids:
                        # 从应用配置中获取top_k参数，默认为5
                        top_k = getattr(application, 'top_k', 5)
                        logger.info(f"应用引用分段数(top_k): {top_k}")
                        
                        # 合并所有知识库的检索结果
                        all_results = []
                        for kb_id in knowledge_base_ids:
                            # 从知识库获取配置的向量模型，默认为更适合中文的text2vec-base-Chinese
                            from apps.knowledge.models import KnowledgeBase
                            try:
                                kb = KnowledgeBase.objects.get(id=kb_id)
                                # 检查知识库是否有配置的向量模型
                                if hasattr(kb, 'embedding_model') and kb.embedding_model:
                                    embedding_model = kb.embedding_model
                                    dimension = getattr(kb, 'embedding_dimension', 768)  # text2vec-base-Chinese的维度是768
                                else:
                                    # 默认使用更适合中文的模型
                                    embedding_model = 'text2vec-base-Chinese'
                                    dimension = 768
                            except KnowledgeBase.DoesNotExist:
                                # 默认使用更适合中文的模型
                                embedding_model = 'text2vec-base-Chinese'
                                dimension = 768
                            
                            config = {
                                'knowledge_base_id': kb_id,
                                'embedding_model_name': embedding_model,
                                'dimension': dimension
                            }
                            vector_store = PGVectorStore(config)
                            # 使用混合搜索模式，提高检索准确性
                            results = vector_store.similarity_search(user_message, k=top_k, search_type='blend')
                            all_results.extend(results)
                        
                        # 按相似度排序，取前top_k个结果
                        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                        top_results = all_results[:top_k]
                        
                        # 检查相似度阈值，只有当相关性足够高时才使用知识库内容
                        if top_results:
                            # 动态调整相似度阈值
                            # 1. 获取基础阈值
                            base_threshold = getattr(application, 'similarity_threshold', 0.5)
                            
                            # 2. 根据搜索类型调整阈值
                            search_types = set(result.get('search_type', 'embedding') for result in top_results)
                            logger.info(f"搜索结果类型: {search_types}")
                            
                            # 关键词搜索和混合搜索可以使用较低的阈值
                            if 'keywords' in search_types or 'blend' in search_types:
                                similarity_threshold = max(base_threshold * 0.8, 0.3)  # 最低不低于0.3
                            else:
                                similarity_threshold = base_threshold
                            
                            # 3. 根据结果质量动态调整
                            # 如果所有结果分数都很低，适当降低阈值
                            avg_score = sum(result.get('score', 0) for result in top_results) / len(top_results)
                            if avg_score < similarity_threshold and len(top_results) > 0:
                                # 取最高分数的80%作为阈值，但不低于0.2
                                similarity_threshold = max(max(result.get('score', 0) for result in top_results) * 0.8, 0.2)
                            
                            logger.info(f"应用基础阈值: {base_threshold}, 动态调整后阈值: {similarity_threshold}, 平均分数: {avg_score}")
                            
                            # 筛选出相似度高于阈值的结果
                            relevant_results = [result for result in top_results if result.get('score', 0) >= similarity_threshold]
                            logger.info(f"相关结果数量: {len(relevant_results)}/{len(top_results)}")
                            
                            if relevant_results:
                                for i, result in enumerate(relevant_results):
                                    content = result.get('content', '')
                                    knowledge_context += f"{content}\n\n"
                                logger.info(f"知识库检索结果: {len(relevant_results)}条，已添加到提示词")
                            else:
                                # 如果没有相关结果，尝试使用所有结果（降低阈值到0）
                                logger.info("所有结果相似度低于阈值，尝试使用所有结果")
                                for i, result in enumerate(top_results):
                                    content = result.get('content', '')
                                    knowledge_context += f"{content}\n\n"
                                logger.info(f"知识库检索结果: {len(top_results)}条，已添加到提示词")
                        else:
                            logger.info("知识库检索未找到相关结果")
                    else:
                        logger.info("应用未关联任何知识库")
                except Exception as e:
                    logger.error(f"知识库检索失败: {e}")
                
                # 获取应用信息
                from apps.application.models import Application
                application = Application.objects.get(id=application_id)
                
                # 获取应用的系统提示和提示词模板
                system_prompt = getattr(application, 'system_prompt', '')
                prompt_template_type = getattr(application, 'prompt_template_type', 'DEFAULT')
                
                # 导入提示词模板和生成函数
                from apps.chat.prompt_templates import generate_prompt
                
                # 获取应用关联的模型配置
                model_config = getattr(application, 'model_config', {})
                
                # 解析模型配置字段（处理可能的JSON字符串）
                if isinstance(model_config, str):
                    import json
                    model_config = json.loads(model_config)
                elif not isinstance(model_config, dict):
                    model_config = {}
                
                # 获取历史聊天记录数量配置
                history_count = model_config.get('history_count', 5)  # 默认获取最近5条对话记录
                logger.info(f"历史聊天记录数量: {history_count}")
                
                # 获取历史聊天记录
                history_messages = []
                if history_count > 0:
                    try:
                        # 获取当前会话的历史消息，按时间倒序，取最近的history_count条
                        history_queryset = ChatMessage.objects.filter(
                            session_id=session_id,
                            is_delete=False
                        ).order_by('-create_time')[:history_count]
                        
                        # 将历史消息转换为列表，并按时间正序排列
                        history_messages = list(history_queryset)[::-1]
                        logger.info(f"获取到历史聊天记录: {len(history_messages)}条")
                    except Exception as e:
                        logger.error(f"获取历史聊天记录失败: {e}")
                
                # 构建历史聊天记录字符串
                history_context = ""
                if history_messages:
                    for msg in history_messages:
                        role = "用户" if msg.role == "user" else "AI助手"
                        history_context += f"{role}: {msg.content}\n\n"
                
                # 构建文件信息字符串（仅在启用文件上传时）
                files_context = ""
                if enable_file_upload and file_list:
                    files_context = "\n\n用户上传了以下文件：\n"
                    for i, file_info in enumerate(file_list, 1):
                        files_context += f"{i}. {file_info.get('name', file_info.get('file_name', '未知文件'))} (类型: {file_info.get('type', 'document')})\n"
                
                # 使用generate_prompt函数生成最终提示词
                prompt = generate_prompt(
                    template_type=prompt_template_type,
                    system_prompt=system_prompt,
                    question=user_message,
                    context=knowledge_context,
                    history=history_context,
                    files=files_context
                )
                
                # 获取模型配置信息
                model_id = model_config.get('model', '')
                model_type = model_config.get('model_type', 'LLM')
                model_name = model_config.get('model_name', 'mimo-v2-flash')
                provider_key = model_config.get('provider', 'openai')
                
                # 如果配置了model_id，使用对应的模型配置
                if model_id:
                    try:
                        from apps.model_provider.models import ModelConfig
                        model_instance = ModelConfig.objects.get(id=model_id, is_delete=False, is_active=True)
                        # 确保model_config始终是字典类型
                        model_config = model_instance.params
                        if isinstance(model_config, str):
                            import json
                            model_config = json.loads(model_config)
                        elif not isinstance(model_config, dict):
                            model_config = {}
                        model_type = model_instance.model_type
                        model_name = model_instance.model
                        provider_key = model_instance.provider
                        logger.info(f"使用模型ID {model_id} 对应的模型配置: {provider_key}::{model_name}, 类型: {model_type}")
                    except ModelConfig.DoesNotExist:
                        logger.warning(f"模型ID {model_id} 不存在或已被删除，使用默认模型配置")
                    except Exception as e:
                        logger.error(f"获取模型ID {model_id} 对应的配置失败: {e}")
                
                logger.info(f"使用模型: {provider_key}::{model_name}，类型: {model_type}")
                
                # 获取模型提供商
                provider = global_provider_manager.get_provider(provider_key)
                if not provider:
                    raise ValueError(f"未知的模型提供商: {provider_key}")
                
                # 获取模型认证信息
                from dotenv import load_dotenv
                load_dotenv()
                
                model_credential = {
                    'api_key': os.getenv('LLM_API_KEY', ''),
                    'base_url': os.getenv('LLM_BASE_URL', 'https://api.xiaomimimo.com/v1').rstrip('/chat/completions').rstrip('/'),
                    'model': model_name,
                    'temperature': model_config.get('temperature', 0.7)
                }
                
                # 添加输出思考配置
                output_thinking = model_config.get('output_thinking', False)
                model_kwargs = {}
                
                # 获取模型实例
                model = provider.get_model(model_type, model_name, model_credential, **model_kwargs)
                
                # 调用大模型生成回复 - 使用流式请求
                response = model.stream(prompt)
                
                # 收集所有流式响应内容
                assistant_message = ""
                has_content = False
                for chunk in response:
                    content = chunk.content
                    if content:
                        has_content = True
                        assistant_message += content
                
                # 如果没有流式数据，使用invoke作为备选
                if not has_content:
                    response = model.invoke(prompt)
                    assistant_message = response.content
                
                # 估算tokens数量（平均每个token约4个字符）
                estimated_tokens = len(assistant_message) // 4 + len(prompt) // 4
                
                result = {'status': 'success', 'context': {'final_response': assistant_message}}
            
            ChatMessage.objects.create(
                session_id=session_id,
                role='assistant',
                content=assistant_message,
                tokens=estimated_tokens
            )
            
            # 更新会话名称 - 根据问答内容生成摘要
            session = ChatSession.objects.get(id=session_id)
            # 只有当会话名称是默认值或未被自定义时才生成摘要
            if session.session_name in ['新建对话', '新会话', '会话1', '会话2', '会话3', '会话4', '会话5']:
                # 使用用户问题和AI回答生成会话摘要
                summary_prompt = f"""请将以下对话内容总结为一个简洁的会话标题，最多15个中文字符，不要使用任何标点符号：
用户：{user_message}
AI：{assistant_message}"""
                
                try:
                    # 获取应用的模型配置
                    from apps.application.models import Application
                    application = Application.objects.get(id=application_id)
                    
                    # 获取应用关联的模型配置
                    model_config = getattr(application, 'model_config', {})
                    if isinstance(model_config, str):
                        import json
                        model_config = json.loads(model_config)
                    elif not isinstance(model_config, dict):
                        model_config = {}
                    
                    # 获取模型配置信息
                    model_id = model_config.get('model', '')
                    model_type = model_config.get('model_type', 'LLM')
                    model_name = model_config.get('model_name', 'mimo-v2-flash')
                    provider_key = model_config.get('provider', 'openai')
                    
                    # 如果配置了model_id，使用对应的模型配置
                    if model_id:
                        from apps.model_provider.models import ModelConfig
                        model_instance = ModelConfig.objects.get(id=model_id, is_delete=False, is_active=True)
                        # 确保model_config始终是字典类型
                        model_config = model_instance.params
                        if isinstance(model_config, str):
                            import json
                            model_config = json.loads(model_config)
                        elif not isinstance(model_config, dict):
                            model_config = {}
                        model_type = model_instance.model_type
                        model_name = model_instance.model
                        provider_key = model_instance.provider
                    
                    # 获取模型认证信息
                    from dotenv import load_dotenv
                    import os
                    load_dotenv()
                    
                    model_credential = {
                        'api_key': os.getenv('LLM_API_KEY', ''),
                        'base_url': os.getenv('LLM_BASE_URL', 'https://api.xiaomimimo.com/v1').rstrip('/chat/completions').rstrip('/'),
                        'model': model_name,
                        'temperature': 0.1  # 低温度确保摘要准确简洁
                    }
                    
                    # 获取模型实例
                    provider = global_provider_manager.get_provider(provider_key)
                    model = provider.get_model(model_type, model_name, model_credential)
                    
                    # 调用大模型生成摘要
                    summary_response = model.invoke(summary_prompt)
                    session_name = summary_response.content.strip()
                    
                    # 确保摘要长度不超过15个字符
                    if len(session_name) > 15:
                        session_name = session_name[:15]
                    
                    # 更新会话名称
                    session.session_name = session_name
                    session.save()
                except Exception as e:
                    # 如果生成摘要失败，使用默认名称加序号
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"生成会话摘要失败: {e}")
                    # 保留原名称
            
            # 构建检索结果返回数据
            search_results = []
            # 确保knowledge_base_ids和top_results在使用前已定义
            if 'knowledge_base_ids' in locals() and 'top_results' in locals() and knowledge_base_ids and top_results:
                for result in top_results:
                    search_results.append({
                        'id': result.get('id', ''),
                        'content': result.get('content', ''),
                        'title': result.get('title', ''),
                        'score': result.get('score', 0)
                    })
            
            return Response({
                'session_id': session_id,
                'user_message': user_message,
                'assistant_message': assistant_message,
                'workflow_result': result,
                'search_results': search_results
            })
        except Exception as e:
            # 记录错误并返回友好信息
            assistant_message = f"抱歉，处理您的请求时出现错误：{str(e)}"
            error_tokens = len(assistant_message) // 4
            
            ChatMessage.objects.create(
                session_id=session_id,
                role='assistant',
                content=assistant_message,
                tokens=error_tokens
            )
            
            return Response({
                'session_id': session_id,
                'user_message': user_message,
                'assistant_message': assistant_message,
                'workflow_result': {'status': 'error', 'message': str(e)}
            }, status=status.HTTP_200_OK)
    
    def _is_medical_query(self, message: str) -> bool:
        """判断消息是否涉及问诊相关内容"""
        # 关键词列表，包含问诊相关的词汇
        medical_keywords = [
            '感冒', '发热', '咳嗽', '头痛', '头晕', '腹痛', '腹泻', '呕吐', '恶心',
            '鼻塞', '流鼻涕', '喉咙痛', '乏力', '怕冷', '出汗', '舌苔', '脉象',
            '症状', '辨证', '方剂', '药方', '中药', '治疗', '诊断', '问诊',
            '中医', '西医', '疾病', '不舒服', '难受', '疼痛', '不适',
            '药', '吃什么', '怎么办', '怎么治', '如何治疗'
        ]
        
        # 转换为小写，统一匹配
        message = message.lower()
        
        # 检查是否包含问诊相关关键词
        for keyword in medical_keywords:
            if keyword in message:
                return True
        
        # 只针对明确的医疗相关乱码模式，不泛用标点符号判断
        # 移除了标点符号判断，避免将普通问候误判为医疗查询
        
        return False


class MessageSatisfactionView(APIView):
    """更新消息的满意度评分"""
    
    def post(self, request, message_id):
        """更新消息满意度
        
        请求参数：
        - satisfaction: 1 表示满意，0 表示不满意
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'收到满意度更新请求: message_id={message_id}, data={request.data}')
        
        try:
            satisfaction = request.data.get('satisfaction')
            if satisfaction not in [0, 1]:
                return Response(
                    {'error': 'satisfaction must be 0 or 1'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            message = ChatMessage.objects.get(id=message_id)
            message.satisfaction = satisfaction
            message.save()
            logger.info(f'满意度更新成功: message_id={message_id}, satisfaction={satisfaction}')
            
            return Response({
                'message': '满意度更新成功',
                'satisfaction': satisfaction
            })
            
        except ChatMessage.DoesNotExist:
            return Response(
                {'error': '消息不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FileUploadView(APIView):
    """文件上传视图"""
    
    def post(self, request):
        """处理文件上传的POST请求"""
        try:
            from apps.chat.serializers import FileUploadSerializer
            
            # 验证上传数据
            serializer = FileUploadSerializer(data=request.data, request=request)
            if not serializer.is_valid():
                return Response(
                    {'error': '文件上传失败', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 上传文件
            result = serializer.upload(with_valid=False)
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"文件上传成功，返回结果: {result}")
            
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"文件上传失败: {str(e)}", exc_info=True)
            return Response(
                {'error': f'文件上传失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FileGetView(APIView):
    """文件获取视图"""
    
    def get(self, request, file_id):
        """获取文件的GET请求"""
        try:
            from apps.chat.serializers import FileGetSerializer
            
            # 验证文件ID
            serializer = FileGetSerializer(data={'id': file_id})
            if not serializer.is_valid():
                return Response(
                    {'error': '文件ID无效', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 获取文件
            result = serializer.get()
            
            return Response({
                'success': True,
                'data': result
            }, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"获取文件失败: {str(e)}", exc_info=True)
            return Response(
                {'error': f'获取文件失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SpeechToTextView(APIView):
    """语音转文本视图，用于将音频文件转换为文本"""
    
    def post(self, request):
        """处理语音转文本的POST请求"""
        try:
            # 检查是否有文件上传
            if 'file' not in request.FILES:
                return Response(
                    {'error': '未提供音频文件'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 获取音频文件
            audio_file = request.FILES['file']
            
            # 读取音频文件内容
            audio_content = audio_file.read()
            
            # 获取应用ID，默认使用'default'
            application_id = request.data.get('application_id', 'default')
            
            # 处理应用ID
            if application_id == 'default':
                from apps.application.models import Application
                try:
                    # 获取第一个激活的应用
                    default_app = Application.objects.filter(is_delete=False, is_active=True).order_by('create_time').first()
                    if default_app:
                        application_id = str(default_app.id)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"获取默认应用失败: {str(e)}")
            
            # 获取应用信息
            from apps.application.models import Application
            application = Application.objects.get(id=application_id)
            
            # 获取应用的模型配置
            model_config = getattr(application, 'model_config', {})
            
            # 解析模型配置字段
            if isinstance(model_config, str):
                import json
                model_config = json.loads(model_config)
            elif not isinstance(model_config, dict):
                model_config = {}
            
            # 获取STT模型配置，优先使用语音模型，否则使用默认配置
            stt_model_id = model_config.get('stt_model', '')
            stt_model_type = ModelTypeConst.STT
            stt_model_name = model_config.get('stt_model_name', 'iat')  # 默认使用讯飞的iat模型
            provider_key = model_config.get('stt_provider', 'xunfei')  # 默认使用讯飞提供商
            
            # 如果配置了stt_model_id，使用对应的模型配置
            if stt_model_id:
                try:
                    from apps.model_provider.models import ModelConfig
                    model_instance = ModelConfig.objects.get(id=stt_model_id, is_delete=False, is_active=True)
                    # 确保model_config始终是字典类型
                    model_config = model_instance.params  # 使用正确的属性名params
                    if isinstance(model_config, str):
                        import json
                        model_config = json.loads(model_config)
                    elif not isinstance(model_config, dict):
                        model_config = {}
                    stt_model_type = model_instance.model_type
                    stt_model_name = model_instance.model_name  # 使用正确的属性名model_name
                    provider_key = model_instance.provider
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info(f"使用STT模型ID {stt_model_id} 对应的模型配置: {provider_key}::{stt_model_name}, 类型: {stt_model_type}")
                except ModelConfig.DoesNotExist:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"STT模型ID {stt_model_id} 不存在或已被删除，使用默认模型配置")
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"获取STT模型ID {stt_model_id} 对应的配置失败: {e}")
            
            # 获取模型提供商
            from apps.model_provider.provider_manager import global_provider_manager
            
            # 添加调试日志
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"当前注册的提供商: {list(global_provider_manager.provider_dict.keys())}")
            logger.debug(f"尝试获取提供商: {provider_key}")
            
            provider = global_provider_manager.get_provider(provider_key)
            if not provider:
                return Response(
                    {'error': f'未知的模型提供商: {provider_key}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 构建模型认证信息
            model_credential = {
                'model': stt_model_name
            }
            
            # 如果配置了stt_model_id，使用对应的模型配置的credential
            if stt_model_id:
                from apps.model_provider.models import ModelConfig
                try:
                    model_instance = ModelConfig.objects.get(id=stt_model_id, is_delete=False, is_active=True)
                    # 直接使用模型配置中的认证信息
                    model_credential['credential'] = model_instance.credential
                    model_credential.update(model_instance.credential)
                except ModelConfig.DoesNotExist:
                    pass
            else:
                # 否则从环境变量获取
                from dotenv import load_dotenv
                import os
                load_dotenv()
                
                model_credential.update({
                    'api_key': os.getenv('LLM_API_KEY', ''),
                    'api_secret': os.getenv('XUNFEI_API_SECRET', ''),
                    'app_id': os.getenv('XUNFEI_APP_ID', ''),
                    'base_url': os.getenv('LLM_BASE_URL', '').rstrip('/chat/completions').rstrip('/')
                })
            
            # 添加应用配置中的额外认证信息
            if model_config:
                model_credential.update(model_config)
            
            # 获取模型实例
            try:
                # 将枚举对象转换为字符串，因为模型提供商期望的是字符串类型的model_type
                model_type_str = stt_model_type.name if hasattr(stt_model_type, 'name') else stt_model_type
                
                # 使用BytesIO处理音频内容
                import io
                audio_stream = io.BytesIO(audio_content)
                audio_stream.name = "audio.wav"
                audio_stream.seek(0)
                
                # 获取模型实例
                model = provider.get_model(model_type_str, stt_model_name, model_credential)
                response = model.invoke(audio_stream)
                recognized_text = response.get('text', '')
            except Exception as llm_error:
                # 如果调用失败，记录错误并返回友好提示
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"语音转文字调用失败: {str(llm_error)}")
                return Response(
                    {'error': f'语音转文字调用失败: {str(llm_error)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 返回识别结果
            return Response({
                'text': recognized_text
            })
        except Exception as e:
            # 记录详细错误信息
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"语音识别请求处理失败: {str(e)}", exc_info=True)
            
            # 返回友好的错误信息
            return Response(
                {'error': f'语音识别失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatStreamView(APIView):
    """聊天流式响应视图，用于实时返回AI回复"""
    
    def post(self, request):
        """处理流式响应的POST请求"""
        application_id = request.data.get('application_id')
        user_message = request.data.get('message', '')
        session_id = request.data.get('session_id')
        
        # 检查应用是否启用文件上传功能
        enable_file_upload = True
        try:
            from apps.application.models import Application
            application = Application.objects.get(id=application_id)
            enable_file_upload = getattr(application, 'enable_file_upload', True)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"获取应用文件上传设置失败: {str(e)}，默认启用文件上传")
        
        # 处理文件信息
        files = []
        if enable_file_upload:
            files = request.data.get('files', [])
            if isinstance(files, str):
                import json
                files = json.loads(files)
            elif not isinstance(files, list):
                files = []
        
        # 如果没有消息但有文件，使用默认消息
        if not user_message and files:
            user_message = '请分析上传的文件'
            
        if not user_message:
            # 返回错误信息
            return StreamingHttpResponse(
                self._generate_error_response(f"message is required"),
                content_type='text/plain'
            )
        
        # 处理用户ID，未认证时生成临时UUID
        user_id = request.user.id if hasattr(request.user, 'id') and request.user.id else uuid.uuid4()
        
        # 检查是否使用默认应用ID
        is_default_app = application_id == 'default'
        
        # 处理application_id，对于默认应用，使用固定的UUID或获取第一个激活的应用
        if is_default_app:
            # 导入必要的模块
            import logging
            logger = logging.getLogger(__name__)
            from apps.application.models import Application
            try:
                # 获取第一个激活的应用，按创建时间排序
                default_app = Application.objects.filter(is_delete=False, is_active=True).order_by('create_time').first()
                if default_app:
                    # 使用现有的默认应用
                    application_id = str(default_app.id)
                    logger.info(f"使用现有默认应用: {application_id}, 名称: {default_app.name}")
                else:
                    # 如果没有现有应用，创建一个默认应用
                    logger.info(f"创建新的默认应用")
                    # 生成固定UUID，确保每次使用默认应用时保持一致
                    application_id = str(uuid.uuid5(uuid.NAMESPACE_OID, 'default-application'))
                    # 检查应用是否已存在
                    default_app, created = Application.objects.get_or_create(
                        id=application_id,
                        defaults={
                            'name': '默认应用',
                            'desc': '系统默认应用',
                            'user_id': user_id,
                            'is_active': True
                        }
                    )
                    logger.info(f"{'创建' if created else '使用'}默认应用: {application_id}, 名称: {default_app.name}")
            except Exception as e:
                logger.error(f"处理默认应用失败: {e}")
                # 失败时使用临时UUID作为备选方案
                application_id = str(uuid.uuid4())
        
        try:
            if not session_id:
                session = ChatSession.objects.create(
                    application_id=application_id,
                    user_id=user_id,
                    session_name='新建对话'
                )
                session_id = str(session.id)
            else:
                # 处理UUID转换，将"default"转换为有效UUID
                try:
                    session = ChatSession.objects.get(id=session_id, is_delete=False)
                except (ChatSession.DoesNotExist, ValueError):
                    # 如果session_id无效或不存在，创建新会话
                    logger.info(f"Invalid or non-existent session_id: {session_id}, creating new session")
                    session = ChatSession.objects.create(
                        application_id=application_id,
                        user_id=user_id,
                        session_name='新会话'
                    )
                    session_id = str(session.id)
        except Exception as e:
            # 如果session_id无效或不存在，创建新会话
            logger.info(f"Invalid or non-existent session_id: {session_id}, creating new session")
            session = ChatSession.objects.create(
                application_id=application_id,
                user_id=user_id,
                session_name='新会话'
            )
            session_id = str(session.id)
        
        # 保存用户消息，包含文件信息和tokens
        user_tokens = len(user_message) // 4
        ChatMessage.objects.create(
            session_id=session_id,
            role='user',
            content=user_message,
            files=files,
            tokens=user_tokens
        )
        
        # 生成并返回流式响应，传递文件信息和文件上传开关
        response = StreamingHttpResponse(
            self._generate_streaming_response(application_id, user_message, session_id, is_default_app, files, enable_file_upload),
            content_type='text/plain',
            headers={
                'X-Content-Type-Options': 'nosniff',
                'Cache-Control': 'no-cache'
            }
        )
        return response
    
    def _generate_streaming_response(self, application_id, user_message, session_id, is_default_app=False, files=None, enable_file_upload=True):
        """生成流式响应的生成器函数"""
        files = files or []
        try:
            # 添加日志
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Streaming response for: {user_message}")
            
            # 判断是否是问诊相关内容
            is_medical_query = self._is_medical_query(user_message)
            logger.info(f"Is medical query: {is_medical_query}")
            
            assistant_message = ""
            
            try:
                if is_medical_query and not is_default_app:
                    # 问诊相关内容且不是默认应用，执行完整的工作流
                    logger.info("Executing full workflow for medical query in streaming mode")
                    workflow_manager = TCMWorkflowManager(application_id)
                    result = workflow_manager.execute_diagnosis_workflow([user_message])
                    
                    assistant_message = result.get('context', {}).get('final_response', '')
                    
                    # 将完整结果分块流式返回
                    if assistant_message:
                        # 逐字或逐句返回，实现流式效果
                        for char in assistant_message:
                            yield char
                    else:
                        # 如果工作流没有返回内容，直接调用大模型
                        logger.info("Workflow returned empty response, switching to direct LLM call")
                        is_medical_query = False
            except Exception as workflow_error:
                # 工作流执行失败，直接调用大模型生成回复
                logger.error(f"Workflow execution failed: {workflow_error}")
                is_medical_query = False
            
            if not is_medical_query or is_default_app:
                # 普通对话或工作流执行失败或默认应用，先检索知识库内容，再调用大模型
                logger.info("Executing direct LLM call with knowledge base retrieval in streaming mode")
                import os
                
                # 确保环境变量被正确加载
                from dotenv import load_dotenv
                load_dotenv()
                
                # 检索知识库内容
                knowledge_context = ""
                try:
                    from apps.application.models import Application
                    from apps.knowledge.vector.pg_vector import PGVectorStore
                    
                    # 获取应用关联的知识库
                    application = Application.objects.get(id=application_id)
                    
                    # 解析知识库字段（处理可能的JSON字符串）
                    knowledge_bases = application.knowledge_bases
                    if isinstance(knowledge_bases, str):
                        import json
                        knowledge_bases = json.loads(knowledge_bases)
                    elif not isinstance(knowledge_bases, list):
                        knowledge_bases = []
                    
                    logger.info(f"应用关联的知识库: {knowledge_bases}")
                    
                    # 合并所有知识库的检索结果
                    all_results = []
                    for kb_id in knowledge_bases:
                        config = {
                            'knowledge_base_id': kb_id,
                            'embedding_model_name': 'BAAI/bge-large-zh-v1.5',
                            'dimension': 1024
                        }
                        vector_store = PGVectorStore(config)
                        # 使用应用配置的top_k参数
                        top_k = getattr(application, 'top_k', 5)
                        results = vector_store.similarity_search(user_message, k=top_k)
                        all_results.extend(results)
                    
                    # 按相似度排序，取前top_k个结果
                    all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                    top_results = all_results[:top_k]
                    
                    # 检查相似度阈值，只有当相关性足够高时才使用知识库内容
                    if top_results:
                        # 获取应用的相似度阈值，默认为0.5
                        similarity_threshold = getattr(application, 'similarity_threshold', 0.5)
                        logger.info(f"应用相似度阈值: {similarity_threshold}")
                        
                        # 筛选出相似度高于阈值的结果
                        relevant_results = [result for result in top_results if result.get('score', 0) >= similarity_threshold]
                        logger.info(f"相关结果数量: {len(relevant_results)}/{len(top_results)}")
                        
                        if relevant_results:
                            knowledge_context = ""
                            for i, result in enumerate(relevant_results):
                                content = result.get('content', '')
                                knowledge_context += f"{content}\n\n"
                            logger.info(f"知识库检索结果: {len(relevant_results)}条，已添加到提示词")
                        else:
                            logger.info("所有结果相似度低于阈值，不添加到提示词")
                    else:
                        logger.info("知识库检索未找到相关结果")
                except Exception as e:
                    logger.error(f"知识库检索失败: {e}")
                
                # 获取应用信息
                from apps.application.models import Application
                application = Application.objects.get(id=application_id)
                
                # 获取应用的系统提示和提示词模板
                system_prompt = getattr(application, 'system_prompt', '')
                prompt_template_type = getattr(application, 'prompt_template_type', 'DEFAULT')
                
                # 导入提示词模板和生成函数
                from apps.chat.prompt_templates import generate_prompt
                
                # 获取应用关联的模型配置
                model_config = getattr(application, 'model_config', {})
                
                # 解析模型配置字段（处理可能的JSON字符串）
                if isinstance(model_config, str):
                    import json
                    model_config = json.loads(model_config)
                elif not isinstance(model_config, dict):
                    model_config = {}
                
                # 获取历史聊天记录数量配置
                history_count = model_config.get('history_count', 5)  # 默认获取最近5条对话记录
                logger.info(f"历史聊天记录数量: {history_count}")
                
                # 获取历史聊天记录
                history_messages = []
                if history_count > 0:
                    try:
                        # 获取当前会话的历史消息，按时间倒序，取最近的history_count条
                        history_queryset = ChatMessage.objects.filter(
                            session_id=session_id,
                            is_delete=False
                        ).order_by('-create_time')[:history_count]
                        
                        # 将历史消息转换为列表，并按时间正序排列
                        history_messages = list(history_queryset)[::-1]
                        logger.info(f"获取到历史聊天记录: {len(history_messages)}条")
                    except Exception as e:
                        logger.error(f"获取历史聊天记录失败: {e}")
                
                # 构建历史聊天记录字符串
                history_context = ""
                if history_messages:
                    for msg in history_messages:
                        role = "用户" if msg.role == "user" else "AI助手"
                        history_context += f"{role}: {msg.content}\n\n"
                
                # 构建文件信息字符串（仅在启用文件上传时）
                files_context = ""
                if enable_file_upload and files:
                    files_context = "\n\n用户上传了以下文件：\n"
                    for i, file_info in enumerate(files, 1):
                        files_context += f"{i}. {file_info.get('name', file_info.get('file_name', '未知文件'))} (类型: {file_info.get('type', 'document')})\n"
                
                # 使用generate_prompt函数生成最终提示词
                prompt = generate_prompt(
                    template_type=prompt_template_type,
                    system_prompt=system_prompt,
                    question=user_message,
                    context=knowledge_context,
                    history=history_context,
                    files=files_context
                )
                
                # 获取模型配置信息
                model_id = model_config.get('model', '')
                model_type = model_config.get('model_type', 'LLM')
                model_name = model_config.get('model_name', 'mimo-v2-flash')
                provider_key = model_config.get('provider', 'openai')
                
                # 如果配置了model_id，使用对应的模型配置
                if model_id:
                    try:
                        from apps.model_provider.models import ModelConfig
                        model_instance = ModelConfig.objects.get(id=model_id, is_delete=False, is_active=True)
                        # 确保model_config始终是字典类型
                        model_config = model_instance.params
                        if isinstance(model_config, str):
                            import json
                            model_config = json.loads(model_config)
                        elif not isinstance(model_config, dict):
                            model_config = {}
                        model_type = model_instance.model_type
                        model_name = model_instance.model
                        provider_key = model_instance.provider
                        logger.info(f"使用模型ID {model_id} 对应的模型配置: {provider_key}::{model_name}, 类型: {model_type}")
                    except ModelConfig.DoesNotExist:
                        logger.warning(f"模型ID {model_id} 不存在或已被删除，使用默认模型配置")
                    except Exception as e:
                        logger.error(f"获取模型ID {model_id} 对应的配置失败: {e}")
                
                logger.info(f"使用模型: {provider_key}::{model_name}，类型: {model_type}")
                
                # 获取模型提供商
                from apps.model_provider.provider_manager import global_provider_manager
                provider = global_provider_manager.get_provider(provider_key)
                if not provider:
                    raise ValueError(f"未知的模型提供商: {provider_key}")
                
                # 获取模型认证信息
                model_credential = {
                    'api_key': os.getenv('LLM_API_KEY', ''),
                    'base_url': os.getenv('LLM_BASE_URL', 'https://api.xiaomimimo.com/v1').rstrip('/chat/completions').rstrip('/'),
                    'model': model_name,
                    'temperature': model_config.get('temperature', 0.7)
                }
                
                # 添加输出思考配置
                output_thinking = model_config.get('output_thinking', False)
                model_kwargs = {}
                
                # 获取模型实例
                model = provider.get_model(model_type, model_name, model_credential, **model_kwargs)
                
                # 调用大模型生成回复
                response = model.stream(prompt)
                
                # 逐块返回响应内容
                has_content = False
                for chunk in response:
                    content = chunk.content
                    if content:
                        has_content = True
                        assistant_message += content
                        yield content
                        # 添加一个小延迟，确保前端能实时显示
                        import time
                        time.sleep(0.05)
                
                # 如果没有流式数据，返回完整响应
                if not has_content:
                    response = model.invoke(prompt)
                    assistant_message = response.content
                    # 逐字返回，实现流式效果
                    for char in assistant_message:
                        yield char
                        # 添加一个小延迟，确保前端能实时显示
                        import time
                        time.sleep(0.05)
            
            # 估算tokens数量（平均每个token约4个字符）
            estimated_tokens = len(assistant_message) // 4 + len(prompt) // 4
            
            # 保存AI回复
            ChatMessage.objects.create(
                session_id=session_id,
                role='assistant',
                content=assistant_message,
                tokens=estimated_tokens
            )
            
            # 更新会话名称 - 根据问答内容生成摘要
            session = ChatSession.objects.get(id=session_id)
            # 只有当会话名称是默认值或未被自定义时才生成摘要
            if session.session_name in ['新建对话', '新会话', '会话1', '会话2', '会话3', '会话4', '会话5']:
                # 使用用户问题和AI回答生成会话摘要
                summary_prompt = f"""请将以下对话内容总结为一个简洁的会话标题，最多15个中文字符，不要使用任何标点符号：
用户：{user_message}
AI：{assistant_message}"""
                
                try:
                    # 获取应用的模型配置
                    from apps.application.models import Application
                    application = Application.objects.get(id=application_id)
                    
                    # 获取应用关联的模型配置
                    model_config = getattr(application, 'model_config', {})
                    if isinstance(model_config, str):
                        import json
                        model_config = json.loads(model_config)
                    elif not isinstance(model_config, dict):
                        model_config = {}
                    
                    # 获取模型配置信息
                    model_id = model_config.get('model', '')
                    model_type = model_config.get('model_type', 'LLM')
                    model_name = model_config.get('model_name', 'mimo-v2-flash')
                    provider_key = model_config.get('provider', 'openai')
                    
                    # 如果配置了model_id，使用对应的模型配置
                    if model_id:
                        from apps.model_provider.models import ModelConfig
                        model_instance = ModelConfig.objects.get(id=model_id, is_delete=False, is_active=True)
                        # 确保model_config始终是字典类型
                        model_config = model_instance.params
                        if isinstance(model_config, str):
                            import json
                            model_config = json.loads(model_config)
                        elif not isinstance(model_config, dict):
                            model_config = {}
                        model_type = model_instance.model_type
                        model_name = model_instance.model
                        provider_key = model_instance.provider
                    
                    # 获取模型认证信息
                    from dotenv import load_dotenv
                    import os
                    load_dotenv()
                    
                    model_credential = {
                        'api_key': os.getenv('LLM_API_KEY', ''),
                        'base_url': os.getenv('LLM_BASE_URL', 'https://api.xiaomimimo.com/v1').rstrip('/chat/completions').rstrip('/'),
                        'model': model_name,
                        'temperature': 0.1  # 低温度确保摘要准确简洁
                    }
                    
                    # 获取模型实例
                    from apps.model_provider.provider_manager import global_provider_manager
                    provider = global_provider_manager.get_provider(provider_key)
                    model = provider.get_model(model_type, model_name, model_credential)
                    
                    # 调用大模型生成摘要
                    summary_response = model.invoke(summary_prompt)
                    session_name = summary_response.content.strip()
                    
                    # 确保摘要长度不超过15个字符
                    if len(session_name) > 15:
                        session_name = session_name[:15]
                    
                    # 更新会话名称
                    session.session_name = session_name
                    session.save()
                except Exception as e:
                    # 如果生成摘要失败，使用默认名称
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"生成会话摘要失败: {e}")
                    # 保留原名称
            
        except Exception as e:
            # 生成错误响应
            error_message = f"抱歉，处理您的请求时出现错误：{str(e)}"
            yield error_message
            
            # 保存错误信息
            error_tokens = len(error_message) // 4
            ChatMessage.objects.create(
                session_id=session_id,
                role='assistant',
                content=error_message,
                tokens=error_tokens
            )
    
    def _generate_error_response(self, error_message):
        """生成错误响应的生成器函数"""
        yield f"抱歉，处理您的请求时出现错误：{error_message}"
    
    def _is_medical_query(self, message: str) -> bool:
        """判断消息是否涉及问诊相关内容"""
        # 关键词列表，包含问诊相关的词汇
        medical_keywords = [
            '感冒', '发热', '咳嗽', '头痛', '头晕', '腹痛', '腹泻', '呕吐', '恶心',
            '鼻塞', '流鼻涕', '喉咙痛', '乏力', '怕冷', '出汗', '舌苔', '脉象',
            '症状', '辨证', '方剂', '药方', '中药', '治疗', '诊断', '问诊',
            '中医', '西医', '疾病', '不舒服', '难受', '疼痛', '不适',
            '药', '吃什么', '怎么办', '怎么治', '如何治疗'
        ]
        
        # 转换为小写，统一匹配
        message = message.lower()
        
        # 检查是否包含问诊相关关键词
        for keyword in medical_keywords:
            if keyword in message:
                return True
        
        # 只针对明确的医疗相关乱码模式，不泛用标点符号判断
        # 移除了标点符号判断，避免将普通问候误判为医疗查询
        
        return False
