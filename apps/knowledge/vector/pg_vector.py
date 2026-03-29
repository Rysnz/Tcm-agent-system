import uuid
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from sentence_transformers import SentenceTransformer
from apps.knowledge.vector.base_vector import BaseVectorStore
from apps.knowledge.models import Paragraph, Embedding, KnowledgeBase, Document

logger = logging.getLogger('apps')

# 默认嵌入模型配置
DEFAULT_EMBEDDING_MODEL = 'bge-m3'
DEFAULT_EMBEDDING_DIMENSION = 1024

# 项目根目录（从apps/knowledge/vector向上3级）
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class PGVectorStore(BaseVectorStore):
    vector_exists = False
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 记录当前使用的HF_ENDPOINT
        hf_endpoint = os.environ.get('HF_ENDPOINT', 'default')
        logger.info(f"当前使用的HF_ENDPOINT: {hf_endpoint}")
        
        # 获取模型配置，优先使用本地模型
        self.embedding_model_name = config.get('embedding_model', DEFAULT_EMBEDDING_MODEL)
        self.dimension = config.get('dimension', DEFAULT_EMBEDDING_DIMENSION)
        
        try:
            # 初始化嵌入模型
            self.embedding_model = self._load_embedding_model()
            logger.info(f"成功初始化嵌入模型: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"初始化嵌入模型失败: {self.embedding_model_name}, 错误: {str(e)}")
            raise e
        
        self.knowledge_base_id = config.get('knowledge_base_id')
    
    def _load_embedding_model(self) -> SentenceTransformer:
        """
        加载嵌入模型，优先使用本地模型
        """
        # 检查本地模型路径
        local_model_path = os.environ.get('LOCAL_EMBEDDING_MODEL_PATH')
        
        # 默认本地模型路径
        default_local_path = BASE_DIR / 'models' / 'embedding' / 'bge-m3'
        
        # 优先级：环境变量 > 默认本地路径 > Hugging Face
        if local_model_path:
            model_path = Path(local_model_path)
            if not model_path.is_absolute():
                model_path = BASE_DIR / model_path
            
            if model_path.exists():
                logger.info(f"使用环境变量指定的本地模型: {model_path}")
                return SentenceTransformer(str(model_path))
            else:
                logger.warning(f"环境变量指定的模型路径不存在: {model_path}")
        
        # 检查默认本地模型路径
        if default_local_path.exists():
            logger.info(f"使用默认本地模型: {default_local_path}")
            return SentenceTransformer(str(default_local_path))
        
        # 如果本地模型不存在，从Hugging Face下载
        logger.info(f"本地模型不存在，从Hugging Face下载: {self.embedding_model_name}")
        return SentenceTransformer(self.embedding_model_name)
    
    def _get_embedding(self, text: str) -> List[float]:
        """
        获取文本的嵌入向量
        :param text: 输入文本
        :return: 嵌入向量列表
        """
        try:
            # 确保文本长度适中，避免模型处理失败
            if len(text) > 2000:
                import logging
                logger = logging.getLogger('apps')
                logger.warning(f"文本长度超过2000字符，将被截断: {text[:100]}...")
                text = text[:2000]
            
            # 使用模型生成嵌入向量
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            import logging
            logger = logging.getLogger('apps')
            logger.error(f"生成文本嵌入向量失败: {e}, 文本: {text[:100]}...")
            # 返回零向量作为备选方案
            return [0.0] * self.dimension
    
    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] = None) -> List[str]:
        ids = []
        knowledge_base = KnowledgeBase.objects.get(id=self.knowledge_base_id)
        
        # 确保索引存在
        self.ensure_index_exists()
        
        # 批量生成嵌入向量
        embeddings = []
        for text in texts:
            embeddings.append(self._get_embedding(text))
        
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            metadata = metadatas[i] if metadatas and len(metadatas) > i else {}
            paragraph_id = metadata.get('paragraph_id') or str(uuid.uuid4())
            document_id = metadata.get('document_id')
            
            # 获取Document对象
            document = None
            if document_id:
                try:
                    document = Document.objects.get(id=document_id)
                except Document.DoesNotExist:
                    pass
            
            # 检查段落是否已存在
            paragraph, created = Paragraph.objects.get_or_create(
                id=paragraph_id,
                defaults={
                    'content': text,
                    'title': metadata.get('title', ''),
                    'page_number': metadata.get('page_number'),
                    'meta': metadata,
                    'document': document
                }
            )
            
            # 更新段落内容如果已存在
            if not created:
                paragraph.content = text
                paragraph.title = metadata.get('title', '')
                paragraph.page_number = metadata.get('page_number')
                paragraph.meta = metadata
                paragraph.document = document
                paragraph.save()
            
            # 创建 Embedding 对象，参考MaxKB的实现
            embedding_obj = Embedding(
                id=str(uuid.uuid4()),
                source_id=metadata.get('source_id', ''),
                source_type=metadata.get('source_type', 'document'),
                is_active=True,
                knowledge=knowledge_base,
                document=document,
                paragraph=paragraph,
                embedding=embedding,
                meta=metadata
            )
            embedding_obj.save()
            
            ids.append(paragraph_id)
        
        return ids
    
    def batch_save(self, items: List[Dict[str, Any]]) -> List[str]:
        """
        批量保存段落和向量（与add_texts功能相同，但接受不同的数据格式）
        :param items: 包含text和其他元数据的字典列表
        :return: 保存的ID列表
        """
        texts = []
        metadatas = []
        
        for item in items:
            # 提取text字段
            text = item.get('text', '')
            texts.append(text)
            
            # 复制元数据，移除text字段
            metadata = item.copy()
            metadata.pop('text', None)
            metadatas.append(metadata)
        
        return self.add_texts(texts, metadatas)
    
    def similarity_search(self, query: str, k: int = 4, filter: Dict[str, Any] = None, 
                        search_type: str = 'embedding') -> List[Dict[str, Any]]:
        """
        支持多种搜索模式的相似度搜索
        :param query: 查询文本
        :param k: 返回结果数量
        :param filter: 过滤条件
        :param search_type: 搜索类型: embedding(向量搜索), keywords(关键词搜索), blend(混合搜索)
        :return: 搜索结果列表
        """
        if search_type == 'keywords':
            return self.keywords_search(query, k, filter)
        elif search_type == 'blend':
            return self.blend_search(query, k, filter)
        else:  # embedding搜索
            return self.embedding_search(query, k, filter)
    
    def embedding_search(self, query: str, k: int = 4, filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """纯向量搜索"""
        import numpy as np
        import json
        from django.db import connection
        import logging
        logger = logging.getLogger('apps')
        
        query_embedding = self._get_embedding(query)
        query_np = np.array(query_embedding)
        logger.info(f"查询向量维度: {len(query_np)}")
        logger.info(f"查询内容: {query}")
        
        # 构建基础查询
        base_sql = """
            SELECT 
                p.id,
                p.content,
                p.title,
                p.page_number,
                p.meta,
                e.embedding
            FROM tcm_embedding e
            JOIN tcm_paragraph p ON e.paragraph_id = p.id
            WHERE e.knowledge_id = %s
        """
        params = [str(self.knowledge_base_id)]
        
        # 添加过滤条件
        if filter:
            if filter.get('document_id'):
                base_sql += " AND e.document_id = %s"
                params.append(filter['document_id'])
            if filter.get('exclude_document_ids'):
                base_sql += " AND e.document_id NOT IN %s"
                params.append(tuple(filter['exclude_document_ids']))
            if filter.get('exclude_paragraph_ids'):
                base_sql += " AND p.id NOT IN %s"
                params.append(tuple(filter['exclude_paragraph_ids']))
        
        # 查询所有相关的向量记录
        with connection.cursor() as cursor:
            cursor.execute(base_sql, params)
            results = cursor.fetchall()
        
        logger.info(f"查询到 {len(results)} 条向量记录")
        
        # 计算相似度
        similarities = []
        for i, row in enumerate(results):
            # 获取向量数据
            vector_data = row[5]
            # 获取段落内容，用于日志
            paragraph_content = row[1][:50] if len(row[1]) > 50 else row[1]
            
            # 确保向量数据是列表格式
            if isinstance(vector_data, str):
                # 如果是字符串，尝试解析为JSON
                try:
                    vector_data = json.loads(vector_data)
                except json.JSONDecodeError as e:
                    logger.error(f"解析向量JSON失败: {e}")
                    continue
            
            if isinstance(vector_data, list):
                # 计算余弦相似度
                vector_np = np.array(vector_data)
                # 检查向量维度是否匹配
                if len(vector_np) != len(query_np):
                    logger.error(f"向量维度不匹配: 查询向量维度 {len(query_np)}, 存储向量维度 {len(vector_np)}")
                    continue
                
                # 计算点积
                dot_product = np.dot(query_np, vector_np)
                # 计算模长
                query_norm = np.linalg.norm(query_np)
                vector_norm = np.linalg.norm(vector_np)
                # 计算余弦相似度
                if query_norm > 0 and vector_norm > 0:
                    similarity = dot_product / (query_norm * vector_norm)
                else:
                    similarity = 0.0
                
                logger.info(f"记录 {i+1} 相似度: {similarity:.4f}, 内容: {paragraph_content}...")
                
                similarities.append({
                    'id': row[0],
                    'content': row[1],
                    'title': row[2],
                    'page_number': row[3],
                    'metadata': row[4],
                    'score': similarity,
                    'search_type': 'embedding'
                })
            else:
                logger.error(f"向量数据不是列表格式: {type(vector_data)}")
        
        # 按相似度排序，取前k个
        logger.info(f"共计算 {len(similarities)} 条相似度记录")
        similarities.sort(key=lambda x: x['score'], reverse=True)
        
        # 记录排序后的结果
        for i, result in enumerate(similarities[:k]):
            logger.info(f"排序后第 {i+1} 条结果: 相似度 {result['score']:.4f}, 内容: {result['content'][:50]}...")
        
        return similarities[:k]
    
    def keywords_search(self, query: str, k: int = 4, filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        关键词搜索（使用BM25算法）
        
        BM25算法公式：
        BM25(D,Q) = Σ IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D|/avgdl))
        
        其中：
        - IDF(qi) = log((N - df(qi) + 0.5) / (df(qi) + 0.5) + 1)
        - f(qi,D) = 词频（词在文档中出现的次数）
        - |D| = 文档长度
        - avgdl = 平均文档长度
        - k1 = 1.2（词频饱和参数）
        - b = 0.75（文档长度归一化参数）
        """
        import math
        import logging
        from django.db import connection
        logger = logging.getLogger('apps')
        
        logger.info(f"BM25关键词搜索: {query}")
        
        # 提取关键词（支持中文）
        keywords = [kw.strip() for kw in query.split() if kw.strip()]
        
        # 如果没有空格分词，按字符切分（支持中文）
        if not keywords:
            keywords = [query[i:i+2] for i in range(0, len(query), 2)]
        
        # 去重
        keywords = list(set(keywords))
        
        if not keywords:
            return []
        
        logger.info(f"提取的关键词: {keywords}")
        
        # BM25参数
        k1 = 1.2  # 词频饱和参数
        b = 0.75  # 文档长度归一化参数
        
        # 1. 获取所有相关段落
        base_sql = """
            SELECT 
                p.id,
                p.content,
                p.title,
                p.page_number,
                p.meta,
                LENGTH(p.content) as doc_length
            FROM tcm_paragraph p
            JOIN tcm_embedding e ON e.paragraph_id = p.id
            WHERE e.knowledge_id = %s
        """
        params = [str(self.knowledge_base_id)]
        
        # 添加过滤条件
        if filter:
            if filter.get('document_id'):
                base_sql += " AND e.document_id = %s"
                params.append(filter['document_id'])
            if filter.get('exclude_document_ids'):
                base_sql += " AND e.document_id NOT IN %s"
                params.append(tuple(filter['exclude_document_ids']))
            if filter.get('exclude_paragraph_ids'):
                base_sql += " AND p.id NOT IN %s"
                params.append(tuple(filter['exclude_paragraph_ids']))
        
        # 添加关键词匹配条件（至少匹配一个关键词）
        like_conditions = []
        for keyword in keywords:
            patterns = [keyword]
            spaced_keyword = " ".join(keyword)
            if spaced_keyword != keyword:
                patterns.append(spaced_keyword)
            
            for pattern in patterns:
                like_conditions.append("(p.content LIKE %s OR p.title LIKE %s)")
                params.extend([f"%{pattern}%", f"%{pattern}%"])
        
        if like_conditions:
            base_sql += " AND (" + " OR ".join(like_conditions) + ")"
        
        with connection.cursor() as cursor:
            cursor.execute(base_sql, params)
            results = cursor.fetchall()
        
        if not results:
            return []
        
        # 2. 计算平均文档长度
        doc_lengths = [row[5] for row in results]
        avgdl = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1
        
        # 3. 计算文档频率（df）和总文档数（N）
        N = len(results)  # 匹配的文档总数
        
        # 计算每个关键词的文档频率
        df = {}
        for keyword in keywords:
            patterns = [keyword]
            spaced_keyword = " ".join(keyword)
            if spaced_keyword != keyword:
                patterns.append(spaced_keyword)
            
            count = sum(
                1 for row in results
                if any(p in (row[1] or "") or p in (row[2] or "") for p in patterns)
            )
            df[keyword] = count if count > 0 else 1  # 避免除零
        
        # 4. 计算IDF
        idf = {}
        for keyword in keywords:
            idf[keyword] = math.log((N - df[keyword] + 0.5) / (df[keyword] + 0.5) + 1)
        
        # 5. 计算BM25分数
        scored_results = []
        for row in results:
            doc_id = row[0]
            content = row[1] or ""
            title = row[2] or ""
            doc_length = row[5] or 1
            
            # 计算每个关键词的TF
            tf = {}
            for keyword in keywords:
                patterns = [keyword]
                spaced_keyword = " ".join(keyword)
                if spaced_keyword != keyword:
                    patterns.append(spaced_keyword)
                
                count = sum(content.count(p) + title.count(p) for p in patterns)
                tf[keyword] = count
            
            # 计算BM25分数
            bm25_score = 0.0
            for keyword in keywords:
                if tf[keyword] > 0:
                    numerator = tf[keyword] * (k1 + 1)
                    denominator = tf[keyword] + k1 * (1 - b + b * (doc_length / avgdl))
                    bm25_score += idf[keyword] * (numerator / denominator)
            
            scored_results.append({
                'id': doc_id,
                'content': content,
                'title': title,
                'page_number': row[3],
                'metadata': row[4],
                'score': bm25_score,
                'search_type': 'keywords_bm25'
            })
        
        # 6. 按分数排序并归一化到0-1
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        # 归一化
        if scored_results:
            # 只有一个结果时，给予较高的分数
            if len(scored_results) == 1:
                scored_results[0]['score'] = 0.85
            else:
                max_score = scored_results[0]['score']
                min_score = scored_results[-1]['score']
                score_range = max_score - min_score if max_score != min_score else 1.0
                
                for result in scored_results:
                    # 归一化到0.3-1.0范围，避免分数过低
                    normalized = (result['score'] - min_score) / score_range if score_range > 0 else 0.5
                    result['score'] = 0.3 + 0.7 * normalized
        
        logger.info(f"BM25搜索到 {len(scored_results)} 条记录")
        
        return scored_results[:k]
    
    def blend_search(self, query: str, k: int = 4, filter: Dict[str, Any] = None,
                     rrf_k: int = 60) -> List[Dict[str, Any]]:
        """
        混合搜索，使用 RRF（Reciprocal Rank Fusion）融合向量搜索和关键词搜索结果。

        RRF 公式：score(d) = Σ 1 / (k + rank(d))
        其中 k=60 是经典 RRF 超参数，rank(d) 是文档在各子系统中的排名（从1开始）。
        """
        import logging
        logger = logging.getLogger('apps')

        logger.info(f"RRF 混合搜索: {query}")

        # 执行两种搜索（取 2*k 个候选）
        embedding_results = self.embedding_search(query, k * 2, filter)
        keywords_results = self.keywords_search(query, k * 2, filter)

        # 构建排名映射
        embedding_rank: Dict[str, int] = {
            r['id']: idx + 1 for idx, r in enumerate(embedding_results)
        }
        keywords_rank: Dict[str, int] = {
            r['id']: idx + 1 for idx, r in enumerate(keywords_results)
        }

        # 合并所有候选文档
        all_ids = set(embedding_rank.keys()) | set(keywords_rank.keys())

        # 构建文档内容映射
        doc_map: Dict[str, Dict] = {}
        for r in embedding_results:
            doc_map[r['id']] = r
        for r in keywords_results:
            if r['id'] not in doc_map:
                doc_map[r['id']] = r

        # 计算 RRF 分数
        rrf_scores: Dict[str, float] = {}
        for doc_id in all_ids:
            rrf_score = 0.0
            if doc_id in embedding_rank:
                rrf_score += 1.0 / (rrf_k + embedding_rank[doc_id])
            if doc_id in keywords_rank:
                rrf_score += 1.0 / (rrf_k + keywords_rank[doc_id])
            rrf_scores[doc_id] = rrf_score

        # 按 RRF 分数排序
        sorted_ids = sorted(all_ids, key=lambda did: rrf_scores[did], reverse=True)

        # 归一化分数到 0-1 范围
        if rrf_scores:
            max_rrf = max(rrf_scores.values())
            min_rrf = min(rrf_scores.values())
            score_range = max_rrf - min_rrf if max_rrf != min_rrf else 1.0
        else:
            score_range = 1.0

        results = []
        for doc_id in sorted_ids[:k]:
            doc = doc_map[doc_id].copy()
            # 归一化到 0-1 范围
            normalized_score = (rrf_scores[doc_id] - min_rrf) / score_range if score_range > 0 else 0.5
            doc['score'] = normalized_score
            doc['search_type'] = 'blend_rrf'
            # 保留原始 RRF 分数作为参考
            doc['rrf_score'] = rrf_scores[doc_id]
            results.append(doc)

        logger.info(f"RRF 混合搜索返回 {len(results)} 条结果")
        return results
    
    def similarity_search_with_score(self, query: str, k: int = 4, filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        带分数的相似度搜索
        :param query: 查询文本
        :param k: 返回结果数量
        :param filter: 过滤条件
        :return: 带分数的搜索结果列表
        """
        return self.similarity_search(query, k, filter)
    
    def delete(self, ids: List[str]) -> bool:
        try:
            # 删除关联的段落（级联会删除embedding）
            Paragraph.objects.filter(id__in=ids).delete()
            # 额外确保删除embedding记录
            Embedding.objects.filter(paragraph_id__in=ids).delete()
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger('apps')
            logger.error(f"删除向量失败: {e}")
            return False
    
    def delete_by_knowledge_id(self, knowledge_id: str) -> bool:
        """
        根据知识库ID删除向量
        :param knowledge_id: 知识库ID
        :return: 是否成功
        """
        try:
            # 先删除关联的段落
            paragraphs = Paragraph.objects.filter(document__knowledge_base_id=knowledge_id)
            paragraph_ids = list(paragraphs.values_list('id', flat=True))
            Paragraph.objects.filter(id__in=paragraph_ids).delete()
            # 删除embedding记录
            Embedding.objects.filter(knowledge_id=knowledge_id).delete()
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger('apps')
            logger.error(f"根据知识库ID删除向量失败: {e}")
            return False
    
    def delete_by_document_id(self, document_id: str) -> bool:
        """
        根据文档ID删除向量
        :param document_id: 文档ID
        :return: 是否成功
        """
        try:
            # 通过外键关系删除
            paragraphs = Paragraph.objects.filter(document_id=document_id)
            paragraph_ids = list(paragraphs.values_list('id', flat=True))
            # 删除段落和关联的embedding
            paragraphs.delete()
            Embedding.objects.filter(paragraph_id__in=paragraph_ids).delete()
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger('apps')
            logger.error(f"根据文档ID删除向量失败: {e}")
            return False
    
    def delete_by_document_ids(self, document_ids: List[str]) -> bool:
        """
        根据文档ID列表删除向量
        :param document_ids: 文档ID列表
        :return: 是否成功
        """
        try:
            # 通过外键关系删除
            paragraphs = Paragraph.objects.filter(document_id__in=document_ids)
            paragraph_ids = list(paragraphs.values_list('id', flat=True))
            # 删除段落和关联的embedding
            paragraphs.delete()
            Embedding.objects.filter(paragraph_id__in=paragraph_ids).delete()
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger('apps')
            logger.error(f"根据文档ID列表删除向量失败: {e}")
            return False
    
    def delete_by_source_id(self, source_id: str, source_type: str) -> bool:
        """
        根据源ID和源类型删除向量
        :param source_id: 源ID
        :param source_type: 源类型
        :return: 是否成功
        """
        try:
            # 通过元数据中的source_id和source_type删除
            paragraphs = Paragraph.objects.filter(meta__source_id=source_id, meta__source_type=source_type)
            paragraph_ids = list(paragraphs.values_list('id', flat=True))
            return self.delete(paragraph_ids)
        except Exception as e:
            import logging
            logger = logging.getLogger('apps')
            logger.error(f"根据源ID和源类型删除向量失败: {e}")
            return False
    
    def delete_by_source_ids(self, source_ids: List[str], source_type: str) -> bool:
        """
        根据源ID列表和源类型删除向量
        :param source_ids: 源ID列表
        :param source_type: 源类型
        :return: 是否成功
        """
        try:
            # 通过元数据中的source_id和source_type删除
            paragraphs = Paragraph.objects.filter(meta__source_id__in=source_ids, meta__source_type=source_type)
            paragraph_ids = list(paragraphs.values_list('id', flat=True))
            return self.delete(paragraph_ids)
        except Exception as e:
            import logging
            logger = logging.getLogger('apps')
            logger.error(f"根据源ID列表和源类型删除向量失败: {e}")
            return False
    
    def update_by_paragraph_id(self, paragraph_id: str, instance: Dict[str, Any]) -> bool:
        """
        根据段落ID更新向量
        :param paragraph_id: 段落ID
        :param instance: 更新内容
        :return: 是否成功
        """
        try:
            Paragraph.objects.filter(id=paragraph_id).update(**instance)
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger('apps')
            logger.error(f"根据段落ID更新向量失败: {e}")
            return False
    
    def update_by_source_id(self, source_id: str, instance: Dict[str, Any]) -> bool:
        """
        根据源ID更新向量
        :param source_id: 源ID
        :param instance: 更新内容
        :return: 是否成功
        """
        try:
            Paragraph.objects.filter(meta__source_id=source_id).update(**instance)
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger('apps')
            logger.error(f"根据源ID更新向量失败: {e}")
            return False
    
    def create_index(self):
        """
        创建优化的向量索引
        根据向量维度和数据量动态调整索引配置
        """
        from django.db import connection
        import logging
        logger = logging.getLogger('apps')
        
        logger.info(f"开始创建向量索引，向量维度: {self.dimension}")
        
        # 计算合适的列表数量，推荐值为数据量的平方根或100-1000之间
        with connection.cursor() as cursor:
            # 获取当前向量数量
            cursor.execute("SELECT COUNT(*) FROM tcm_embedding WHERE knowledge_id = %s", [self.knowledge_base_id])
            vector_count = cursor.fetchone()[0]
            
            # 动态计算列表数量
            if vector_count < 1000:
                lists = 100
            elif vector_count < 10000:
                lists = 200
            else:
                lists = min(1000, int(vector_count ** 0.5))
            
            logger.info(f"向量数量: {vector_count}, 索引列表数量: {lists}")
            
            # 根据向量维度选择合适的索引类型
            # 对于高维向量，使用ivfflat索引
            index_name = f"tcm_embedding_idx_{self.knowledge_base_id}"
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS "{index_name}" 
                ON tcm_embedding USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = {lists})
                WHERE knowledge_id = '{self.knowledge_base_id}'
            """)
            
            # 同时创建知识库ID的常规索引，加速过滤
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS tcm_embedding_kb_idx
                ON tcm_embedding (knowledge_id)
            """)
            
            # 创建元数据字段的索引
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS tcm_paragraph_meta_idx
                ON tcm_paragraph USING gin(meta jsonb_path_ops)
            """)
            
            logger.info("向量索引创建完成")
    
    def drop_index(self):
        from django.db import connection
        import logging
        logger = logging.getLogger('apps')
        
        with connection.cursor() as cursor:
            cursor.execute(f'DROP INDEX IF EXISTS "tcm_embedding_idx_{self.knowledge_base_id}"')
            logger.info("向量索引删除完成")
    
    def ensure_index_exists(self):
        """
        确保向量索引存在，在向量插入前调用
        """
        from django.db import connection
        import logging
        logger = logging.getLogger('apps')
        
        with connection.cursor() as cursor:
            # 检查索引是否存在
            cursor.execute(f"""
                SELECT 1 FROM pg_indexes 
                WHERE indexname = 'tcm_embedding_idx_{self.knowledge_base_id}'
            """)
            if not cursor.fetchone():
                logger.info("向量索引不存在，开始创建")
                self.create_index()
            else:
                logger.info("向量索引已存在")
    
    def vector_is_create(self) -> bool:
        """
        检查向量库是否已创建
        :return: 是否已创建
        """
        # 项目启动默认是创建好的 不需要再创建
        return True
    
    def vector_create(self):
        """
        创建向量库
        :return: 是否成功
        """
        return True
