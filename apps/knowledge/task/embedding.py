from apps import app
from apps.knowledge.models import Document
from apps.knowledge.task.document_processor import DocumentProcessor
import logging

logger = logging.getLogger('apps')


@app.task
async def process_document_task(document_id: str):
    """
    异步处理文档的Celery任务
    """
    try:
        logger.info(f"开始处理文档: {document_id}")
        
        # 获取文档记录
        document = Document.objects.get(id=document_id)
        
        # 创建处理器实例
        processor = DocumentProcessor(str(document.knowledge_base.id))
        
        # 直接调用处理逻辑
        paragraphs = processor._extract_text(document.file_path, document.file_type)
        processor._process_paragraphs(document, paragraphs)
        
        # 更新文档状态和统计信息
        document.status = 'completed'
        document.char_count = sum(len(p['content']) for p in paragraphs)
        document.paragraph_count = len(paragraphs)
        document.save()
        
        logger.info(f"文档处理完成: {document_id}")
        return True
    except Exception as e:
        logger.error(f"处理文档失败 {document_id}: {str(e)}", exc_info=True)
        # 更新文档状态为failed
        document = Document.objects.get(id=document_id)
        document.status = 'failed'
        document.save()
        return False
