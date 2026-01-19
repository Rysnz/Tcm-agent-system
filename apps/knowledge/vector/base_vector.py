from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseVectorStore(ABC):
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] = None) -> List[str]:
        pass
    
    def save(self, text: str, source_type: str, knowledge_id: str, document_id: str, 
             paragraph_id: str, source_id: str, is_active: bool = True):
        """
        保存单个文本的向量
        :param text: 文本内容
        :param source_type: 源类型
        :param knowledge_id: 知识库ID
        :param document_id: 文档ID
        :param paragraph_id: 段落ID
        :param source_id: 源ID
        :param is_active: 是否激活
        :return: 是否成功
        """
        return self.add_texts([text], [{
            'source_type': source_type,
            'knowledge_id': knowledge_id,
            'document_id': document_id,
            'paragraph_id': paragraph_id,
            'source_id': source_id,
            'is_active': is_active
        }])
    
    def batch_save(self, data_list: List[Dict[str, Any]]):
        """
        批量保存文本向量
        :param data_list: 数据列表
        :return: 是否成功
        """
        texts = [data.get('text') for data in data_list]
        metadatas = data_list
        return self.add_texts(texts, metadatas)
    
    @abstractmethod
    def similarity_search(self, query: str, k: int = 4, filter: Dict[str, Any] = None, 
                        search_type: str = 'embedding') -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def similarity_search_with_score(self, query: str, k: int = 4, filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def delete(self, ids: List[str]) -> bool:
        pass
    
    def delete_by_knowledge_id(self, knowledge_id: str) -> bool:
        """
        根据知识库ID删除向量
        :param knowledge_id: 知识库ID
        :return: 是否成功
        """
        pass
    
    def delete_by_document_id(self, document_id: str) -> bool:
        """
        根据文档ID删除向量
        :param document_id: 文档ID
        :return: 是否成功
        """
        pass
    
    def delete_by_document_ids(self, document_ids: List[str]) -> bool:
        """
        根据文档ID列表删除向量
        :param document_ids: 文档ID列表
        :return: 是否成功
        """
        pass
    
    def delete_by_source_id(self, source_id: str, source_type: str) -> bool:
        """
        根据源ID和源类型删除向量
        :param source_id: 源ID
        :param source_type: 源类型
        :return: 是否成功
        """
        pass
    
    def delete_by_source_ids(self, source_ids: List[str], source_type: str) -> bool:
        """
        根据源ID列表和源类型删除向量
        :param source_ids: 源ID列表
        :param source_type: 源类型
        :return: 是否成功
        """
        pass
    
    def update_by_paragraph_id(self, paragraph_id: str, instance: Dict[str, Any]) -> bool:
        """
        根据段落ID更新向量
        :param paragraph_id: 段落ID
        :param instance: 更新内容
        :return: 是否成功
        """
        pass
    
    def update_by_source_id(self, source_id: str, instance: Dict[str, Any]) -> bool:
        """
        根据源ID更新向量
        :param source_id: 源ID
        :param instance: 更新内容
        :return: 是否成功
        """
        pass
    
    @abstractmethod
    def create_index(self):
        pass
    
    @abstractmethod
    def drop_index(self):
        pass
    
    @abstractmethod
    def vector_is_create(self) -> bool:
        """
        检查向量库是否已创建
        :return: 是否已创建
        """
        pass
    
    @abstractmethod
    def vector_create(self):
        """
        创建向量库
        :return: 是否成功
        """
        pass
