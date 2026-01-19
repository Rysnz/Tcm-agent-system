from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.knowledge.models import KnowledgeBase, Document
from apps.knowledge.serializers import KnowledgeBaseSerializer, DocumentSerializer
from apps.knowledge.vector.pg_vector import PGVectorStore
from apps.knowledge.task.document_processor import DocumentProcessor
import logging

logger = logging.getLogger('apps')

class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeBase.objects.filter(is_delete=False)
    serializer_class = KnowledgeBaseSerializer
    
    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)
    
    @action(detail=True, methods=['post'])
    def create_index(self, request, pk=None):
        """
        创建知识库索引
        """
        knowledge_base = self.get_object()
        config = {
            'knowledge_base_id': str(knowledge_base.id),
            'embedding_model': knowledge_base.embedding_model,
            'dimension': knowledge_base.embedding_dimension
        }
        vector_store = PGVectorStore(config)
        vector_store.create_index()
        return Response({'message': 'Index created successfully'})
    
    @action(detail=True, methods=['post'])
    def drop_index(self, request, pk=None):
        """
        删除知识库索引
        """
        knowledge_base = self.get_object()
        config = {
            'knowledge_base_id': str(knowledge_base.id),
            'embedding_model': knowledge_base.embedding_model,
            'dimension': knowledge_base.embedding_dimension
        }
        vector_store = PGVectorStore(config)
        vector_store.drop_index()
        return Response({'message': 'Index dropped successfully'})
    
    @action(detail=True, methods=['post'])
    def embedding(self, request, pk=None):
        """
        重新生成知识库向量
        """
        knowledge_base = self.get_object()
        # 这里可以添加重新生成向量的逻辑
        return Response({'message': 'Embedding process started'})
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        获取知识库统计信息
        """
        knowledge_base = self.get_object()
        document_count = Document.objects.filter(knowledge_base=knowledge_base, is_delete=False).count()
        
        from apps.knowledge.models import VectorStore
        vector_count = VectorStore.objects.filter(knowledge_base=knowledge_base).count()
        
        return Response({
            'document_count': document_count,
            'vector_count': vector_count,
            'embedding_model': knowledge_base.embedding_model,
            'search_type': knowledge_base.search_type
        })

class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.filter(is_delete=False)
    serializer_class = DocumentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        knowledge_base_id = self.request.query_params.get('knowledge_base')
        if knowledge_base_id:
            queryset = queryset.filter(knowledge_base_id=knowledge_base_id)
        return queryset
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """
        重新处理文档
        """
        document = self.get_object()
        
        # 重置文档状态
        document.status = 'processing'
        document.progress = 0
        document.save()
        
        # 启动异步处理
        import threading
        def reprocess_document():
            try:
                processor = DocumentProcessor(str(document.knowledge_base.id))
                
                # 使用原有文件路径重新处理
                file_path = document.file_path
                file_type = document.file_type
                
                paragraphs = processor._extract_text(file_path, file_type)
                
                # 更新文档统计信息
                document.char_count = sum(len(p['content']) for p in paragraphs)
                document.paragraph_count = len(paragraphs)
                document.progress = 50
                document.save()
                
                # 处理段落
                processor._process_paragraphs(document, paragraphs)
                
                document.status = 'completed'
                document.progress = 100
                document.save()
            except Exception as e:
                logger.error(f"重新处理文档失败: {document.id}, 错误: {str(e)}")
                document.status = 'failed'
                document.progress = 100
                document.save()
        
        thread = threading.Thread(target=reprocess_document, name=f"ReprocessDocument-{document.id}")
        thread.daemon = True
        thread.start()
        
        return Response({'message': 'Document reprocessing started'})
    
    @action(detail=True, methods=['post'])
    def delete_embedding(self, request, pk=None):
        """
        删除文档向量
        """
        document = self.get_object()
        
        config = {
            'knowledge_base_id': str(document.knowledge_base.id),
            'embedding_model': document.knowledge_base.embedding_model,
            'dimension': document.knowledge_base.embedding_dimension
        }
        vector_store = PGVectorStore(config)
        vector_store.delete_by_document_id(str(document.id))
        
        return Response({'message': 'Document embedding deleted successfully'})

class DocumentUploadView(APIView):
    
    def post(self, request):
        """
        上传文档并异步处理
        """
        logger.info(f"Document upload request received: {request.data}")
        logger.info(f"Files received: {request.FILES}")
        
        file = request.FILES.get('file')
        knowledge_base_id = request.data.get('knowledge_base_id')
        
        if not file:
            logger.error("No file provided in request")
            return Response(
                {'error': 'File is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not knowledge_base_id:
            logger.error("No knowledge_base_id provided in request")
            return Response(
                {'error': 'knowledge_base_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 先创建文档记录，返回给前端
            from apps.knowledge.models import KnowledgeBase, Document
            
            knowledge_base = KnowledgeBase.objects.get(id=knowledge_base_id)
            
            # 保存文件到本地
            import os
            import uuid
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            
            file_name = file.name
            file_size = file.size
            file_type = os.path.splitext(file_name)[1].lower().lstrip('.')
            
            # 保存文件
            file_path = default_storage.save(f'documents/{uuid.uuid4()}_{file_name}', ContentFile(file.read()))
            
            # 获取绝对文件路径
            from django.conf import settings
            absolute_file_path = os.path.join(settings.MEDIA_ROOT, file_path)
            
            logger.info(f"文件保存完成: {file_name}, 相对路径: {file_path}, 绝对路径: {absolute_file_path}")
            logger.info(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
            
            # 检查文件是否存在
            if os.path.exists(absolute_file_path):
                logger.info(f"文件存在: {absolute_file_path}, 文件大小: {os.path.getsize(absolute_file_path)} bytes")
            else:
                logger.error(f"文件不存在: {absolute_file_path}")
            
            # 创建文档记录，状态为processing
            document = Document.objects.create(
                knowledge_base=knowledge_base,
                name=file_name,
                file_type=file_type,
                file_size=file_size,
                file_path=absolute_file_path,
                status='processing'
            )
            
            logger.info(f"Document created successfully: {document.id}, status: processing, file_path: {document.file_path}")
            
            # 使用线程异步处理文档
            import threading
            def process_document_async():
                try:
                    # 首先记录线程启动日志
                    logger.info(f"文档处理线程启动: {document.id}, file_path: {absolute_file_path}, file_type: {file_type}")
                    
                    # 初始化进度
                    document.progress = 0
                    document.save()
                    logger.info(f"初始化进度完成: {document.id}")
                    
                    # 再次检查文件是否存在，确保线程中能访问到
                    if os.path.exists(absolute_file_path):
                        logger.info(f"线程中文件存在: {absolute_file_path}, 文件大小: {os.path.getsize(absolute_file_path)} bytes")
                    else:
                        logger.error(f"线程中文件不存在: {absolute_file_path}")
                        # 更新文档状态为failed
                        document.status = 'failed'
                        document.progress = 100
                        document.save()
                        return
                    
                    # 创建处理器实例
                    logger.info(f"创建处理器实例: {document.id}")
                    processor = DocumentProcessor(knowledge_base_id)
                    logger.info(f"处理器实例创建成功: {document.id}")
                    
                    # 提取文本
                    logger.info(f"开始提取文本: {document.id}, 文件路径: {absolute_file_path}, 文件类型: {file_type}")
                    paragraphs = processor._extract_text(absolute_file_path, file_type)
                    logger.info(f"提取文本完成，共{len(paragraphs)}段: {document.id}")
                    
                    # 添加更详细的日志，显示前3个段落的内容
                    for i, para in enumerate(paragraphs[:3]):
                        logger.info(f"段落{i+1}内容: {para['content'][:100]}...")
                    
                    document.progress = 50
                    document.char_count = sum(len(p['content']) for p in paragraphs)
                    document.paragraph_count = len(paragraphs)
                    document.save()
                    logger.info(f"进度更新为50%: {document.id}")
                    
                    try:
                        # 处理段落和生成向量
                        logger.info(f"开始处理段落和生成向量: {document.id}")
                        processor._process_paragraphs(document, paragraphs)
                        logger.info(f"处理段落和生成向量完成: {document.id}")
                        
                        document.progress = 100
                        document.status = 'completed'
                        document.save()
                        logger.info(f"文档处理完成: {document.id}, 字符数: {document.char_count}, 段落数: {document.paragraph_count}")
                        
                        # 验证向量存储是否成功
                        from apps.knowledge.models import Embedding
                        vector_count = Embedding.objects.filter(paragraph__document=document).count()
                        logger.info(f"文档向量存储数量: {vector_count}, 段落数量: {document.paragraph_count}")
                    except Exception as vector_error:
                        logger.error(f"向量化处理失败: {document.id}, 错误类型: {type(vector_error).__name__}, 错误信息: {str(vector_error)}", exc_info=True)
                        # 向量化失败时，文档状态设置为partially_completed，保留已处理的文本信息
                        document.status = 'partially_completed'
                        document.save()
                        logger.info(f"文档部分处理完成: {document.id}, 字符数: {document.char_count}, 段落数: {document.paragraph_count}")
                except Exception as e:
                    logger.error(f"处理文档时发生异常: {document.id}, 错误类型: {type(e).__name__}, 错误信息: {str(e)}", exc_info=True)
                    # 更新文档状态为failed
                    try:
                        document.status = 'failed'
                        # 如果进度还是0，说明在早期阶段失败
                        if document.progress == 0:
                            document.progress = 100
                        document.save()
                        logger.info(f"异常状态更新完成: {document.id}, 最终进度: {document.progress}%")
                    except Exception as update_error:
                        logger.error(f"更新异常状态失败: {document.id}, 错误: {str(update_error)}")
            
            # 启动异步线程处理文档
            logger.info(f"准备启动文档处理线程: {document.id}")
            thread = threading.Thread(target=process_document_async, name=f"DocumentProcessor-{document.id}")
            thread.daemon = True
            thread.start()
            logger.info(f"文档处理线程已启动: {document.id}, 线程ID: {thread.ident}")
            
            # 立即返回响应给前端
            return Response({
                'message': 'Document upload accepted, processing in background',
                'document_id': str(document.id)
            })
        except Exception as e:
            logger.error(f"Error handling document upload: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Error handling document upload: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class KnowledgeSearchView(APIView):
    
    def post(self, request):
        """
        知识库检索接口
        """
        knowledge_base_id = request.data.get('knowledge_base_id')
        query = request.data.get('query', '')
        
        if not knowledge_base_id:
            return Response(
                {'error': 'knowledge_base_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取知识库配置
        try:
            knowledge_base = KnowledgeBase.objects.get(id=knowledge_base_id)
        except KnowledgeBase.DoesNotExist:
            return Response(
                {'error': 'Knowledge base not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 使用请求参数或知识库默认配置
        top_k = int(request.data.get('top_k', knowledge_base.top_k))
        search_type = request.data.get('search_type', knowledge_base.search_type)
        similarity_threshold = float(request.data.get('similarity_threshold', knowledge_base.similarity_threshold))
        
        config = {
            'knowledge_base_id': knowledge_base_id,
            'embedding_model': knowledge_base.embedding_model,
            'dimension': knowledge_base.embedding_dimension
        }
        
        vector_store = PGVectorStore(config)
        results = vector_store.similarity_search(query, k=top_k, search_type=search_type)
        
        # 应用相似度阈值过滤
        filtered_results = [result for result in results if result['score'] >= similarity_threshold]
        
        return Response({
            'query': query,
            'knowledge_base_id': knowledge_base_id,
            'search_type': search_type,
            'top_k': top_k,
            'similarity_threshold': similarity_threshold,
            'results_count': len(filtered_results),
            'results': filtered_results
        })

class EmbeddingOperationView(APIView):
    """
    向量操作接口
    """
    
    def post(self, request):
        """
        执行向量操作
        """
        operation = request.data.get('operation')
        knowledge_base_id = request.data.get('knowledge_base_id')
        
        if not operation or not knowledge_base_id:
            return Response(
                {'error': 'operation and knowledge_base_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            knowledge_base = KnowledgeBase.objects.get(id=knowledge_base_id)
            config = {
                'knowledge_base_id': knowledge_base_id,
                'embedding_model': knowledge_base.embedding_model,
                'dimension': knowledge_base.embedding_dimension
            }
            vector_store = PGVectorStore(config)
            
            if operation == 'delete_by_document_ids':
                # 删除多个文档的向量
                document_ids = request.data.get('document_ids', [])
                if not isinstance(document_ids, list):
                    return Response(
                        {'error': 'document_ids must be a list'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                vector_store.delete_by_document_ids(document_ids)
                return Response({'message': 'Embeddings deleted successfully'})
            
            elif operation == 'delete_by_knowledge_id':
                # 删除整个知识库的向量
                vector_store.delete_by_knowledge_id(knowledge_base_id)
                return Response({'message': 'Knowledge base embeddings deleted successfully'})
            
            else:
                return Response(
                    {'error': f'Unknown operation: {operation}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except KnowledgeBase.DoesNotExist:
            return Response(
                {'error': 'Knowledge base not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"向量操作失败: {operation}, 错误: {str(e)}")
            return Response(
                {'error': f'Embedding operation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
