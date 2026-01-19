import os
import sys
import threading
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apps.tcm.settings')

# 初始化Django
import django
django.setup()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('reprocess_documents')

# 导入所需模型和类
from apps.knowledge.models import Document
from apps.knowledge.task.document_processor import DocumentProcessor
from django.conf import settings

# 查找所有状态不是completed的文档，包括failed、partially_completed和processing
documents = Document.objects.exclude(status='completed')
logger.info(f"找到 {documents.count()} 个需要重新处理的文档")

# 处理每个文档
def reprocess_document(document):
    logger.info(f"开始重新处理文档: {document.id}, 名称: {document.name}")
    
    try:
        # 检查文件是否存在
        file_path = document.file_path
        if os.path.exists(file_path):
            logger.info(f"文件存在: {file_path}, 文件大小: {os.path.getsize(file_path)} bytes")
        else:
            logger.error(f"文件不存在: {file_path}")
            # 尝试修复文件路径
            if not file_path.startswith(settings.MEDIA_ROOT):
                logger.info(f"尝试修复文件路径，添加MEDIA_ROOT前缀")
                # 提取相对路径
                if file_path.startswith('documents/'):
                    file_path = os.path.join(settings.MEDIA_ROOT, file_path)
                    logger.info(f"修复后的文件路径: {file_path}")
                elif file_path.startswith('D:/demo/TCM-Agent-System/apps/media/'):
                    # 已经是正确的绝对路径
                    pass
                else:
                    logger.error(f"无法修复文件路径: {file_path}")
                    return
            
            # 再次检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"修复后文件仍不存在: {file_path}")
                document.status = 'failed'
                document.progress = 100
                document.save()
                return
        
        # 创建处理器实例
        processor = DocumentProcessor(str(document.knowledge_base.id))
        logger.info(f"处理器实例创建成功: {document.id}")
        
        # 1. 提取文本阶段 - 30%
        logger.info(f"开始提取文本: {document.id}, 文件路径: {file_path}, 文件类型: {document.file_type}")
        paragraphs = processor._extract_text(file_path, document.file_type)
        logger.info(f"提取文本完成，共{len(paragraphs)}段: {document.id}")
        
        document.progress = 30
        document.save()
        logger.info(f"进度更新为30%: {document.id}")
        
        # 2. 保存段落阶段 - 60%
        logger.info(f"开始保存段落: {document.id}")
        processor._save_paragraphs(document, paragraphs)
        logger.info(f"保存段落完成: {document.id}")
        
        document.progress = 60
        document.save()
        logger.info(f"进度更新为60%: {document.id}")
        
        # 3. 向量化阶段 - 90%
        logger.info(f"开始向量化处理: {document.id}")
        processor._vectorize_paragraphs(document, paragraphs)
        logger.info(f"向量化处理完成: {document.id}")
        
        document.progress = 90
        document.save()
        logger.info(f"进度更新为90%: {document.id}")
        
        # 4. 完成阶段 - 100%
        document.status = 'completed'
        document.char_count = sum(len(p['content']) for p in paragraphs)
        document.paragraph_count = len(paragraphs)
        document.progress = 100
        document.save()
        logger.info(f"文档处理完成: {document.id}, 字符数: {document.char_count}, 段落数: {document.paragraph_count}")
    except Exception as e:
        logger.error(f"处理文档时发生异常: {document.id}, 错误类型: {type(e).__name__}, 错误信息: {str(e)}", exc_info=True)
        document.status = 'failed'
        document.progress = 100
        document.save()
        logger.info(f"文档状态更新为failed: {document.id}")

# 为每个文档启动一个线程进行处理
threads = []
for document in documents:
    thread = threading.Thread(target=reprocess_document, args=(document,), name=f"Reprocessor-{document.id}")
    threads.append(thread)
    thread.daemon = True
    thread.start()
    logger.info(f"启动处理线程: {document.id}, 线程ID: {thread.ident}")

# 等待所有线程完成
for thread in threads:
    thread.join()

logger.info("所有文档重新处理完成")
