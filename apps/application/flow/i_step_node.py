from typing import Dict, Any, List
from abc import ABC, abstractmethod
from datetime import datetime

class IStepNode(ABC):
    
    def __init__(self, node_id: str, node_data: Dict[str, Any]):
        self.node_id = node_id
        self.node_data = node_data
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        pass

class StartNode(IStepNode):
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        context['start_time'] = datetime.now()
        return {'status': 'success', 'context': context}
    
    def validate(self) -> bool:
        return True

class LLMNode(IStepNode):
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from langchain_openai import ChatOpenAI
        import os
        import logging
        from django.conf import settings
        
        # 设置日志记录
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        try:
            model_config = self.node_data.get('model_config', {})
            
            # 确保环境变量被正确加载
            from dotenv import load_dotenv
            load_dotenv()
            
            # 获取配置 - 优先级：节点配置 > 环境变量 > 默认值
            model = model_config.get('model') or os.getenv('LLM_MODEL') or 'mimo-v2-flash'
            api_key = model_config.get('api_key') or os.getenv('LLM_API_KEY')
            # 从base_url中移除可能的/chat/completions后缀，因为ChatOpenAI客户端会自动添加
            raw_base_url = model_config.get('base_url') or os.getenv('LLM_BASE_URL') or 'https://api.xiaomimimo.com/v1'
            # 确保base_url只包含API的基础路径，不包含具体的端点路径
            base_url = raw_base_url.rstrip('/chat/completions').rstrip('/')
            temperature = model_config.get('temperature', 0.3)
            
            logger.info(f"Initializing ChatOpenAI with: model={model}, base_url={base_url}, temperature={temperature}")
            
            # 确保API密钥存在
            if not api_key:
                raise ValueError("API key is required for LLM execution")
            
            # 初始化ChatOpenAI客户端
            llm = ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url=base_url,
                temperature=temperature
            )
            
            prompt = self._build_prompt(context)
            logger.info(f"Built prompt: {prompt}")
            
            response = llm.invoke(prompt)
            logger.info(f"Received response: {response}")
            
            context['llm_response'] = response.content
            logger.info(f"LLM response content: {context['llm_response']}")
            
            # 解析JSON格式的症状信息
            import json
            import re
            
            # 提取JSON字符串（去除可能的代码块标记）
            llm_content = response.content
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_content, re.DOTALL)
            if json_match:
                try:
                    symptoms_data = json.loads(json_match.group(1))
                    # 将解析后的症状信息存储到context中
                    context['extracted_symptoms'] = [
                        symptoms_data.get('main_symptoms', ''),
                        symptoms_data.get('accompanying_symptoms', '')
                    ]
                    logger.info(f"Extracted symptoms: {context['extracted_symptoms']}")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse LLM response as JSON: {e}")
            
            return {'status': 'success', 'context': context}
        except Exception as e:
            logger.error(f"Error in LLMNode.execute: {str(e)}", exc_info=True)
            context['llm_error'] = str(e)
            return {'status': 'error', 'message': f'LLM execution failed: {str(e)}', 'context': context}
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        prompt_template = self.node_data.get('prompt_template', '')
        return prompt_template.format(**context)
    
    def validate(self) -> bool:
        return 'model_config' in self.node_data

class KnowledgeRetrievalNode(IStepNode):
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        import logging
        import requests
        from django.conf import settings
        
        logger = logging.getLogger(__name__)
        
        try:
            knowledge_base_id = self.node_data.get('knowledge_base_id')
            query = context.get('user_query', '')
            top_k = self.node_data.get('top_k', 5)
            
            if not knowledge_base_id:
                logger.warning("No knowledge_base_id configured, skipping retrieval")
                context['retrieved_docs'] = []
                return {'status': 'success', 'context': context}
            
            logger.info(f"Performing knowledge retrieval: knowledge_base_id={knowledge_base_id}, query={query}")
            
            response = requests.post(
                f'http://127.0.0.1:8000/api/knowledge/search/',
                json={
                    'knowledge_base_id': knowledge_base_id,
                    'query': query,
                    'top_k': top_k
                },
                timeout=30
            )
            
            if response.status_code == 200:
                search_result = response.json()
                results = search_result.get('results', [])
                context['retrieved_docs'] = results
                logger.info(f"Retrieved {len(results)} documents from knowledge base")
            else:
                logger.error(f"Knowledge search failed: {response.text}")
                context['retrieved_docs'] = []
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to knowledge search service: {str(e)}", exc_info=True)
            context['retrieved_docs'] = []
        except Exception as e:
            logger.error(f"Failed to retrieve documents from knowledge base: {str(e)}", exc_info=True)
            context['retrieved_docs'] = []
        
        return {'status': 'success', 'context': context}
    
    def validate(self) -> bool:
        return 'knowledge_base_id' in self.node_data

class ToolCallNode(IStepNode):
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        tool_name = self.node_data.get('tool_name')
        tool_params = self._extract_params(context)
        
        result = self._call_tool(tool_name, tool_params)
        context['tool_result'] = result
        
        return {'status': 'success', 'context': context}
    
    def _extract_params(self, context: Dict[str, Any]) -> Dict[str, Any]:
        param_mapping = self.node_data.get('param_mapping', {})
        return {k: context.get(v) for k, v in param_mapping.items()}
    
    def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        from apps.tools.tcm_tools import TCMTools
        tools = TCMTools()
        return tools.call(tool_name, params)
    
    def validate(self) -> bool:
        return 'tool_name' in self.node_data

class EndNode(IStepNode):
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)
        
        context['end_time'] = datetime.now()
        
        # 整合所有节点的结果，生成完整的中医问诊回复
        llm_response = context.get('llm_response', '')
        tool_result = context.get('tool_result', {})
        retrieved_docs = context.get('retrieved_docs', [])
        
        # 生成最终回复
        final_response = self._generate_final_response(llm_response, tool_result, retrieved_docs)
        context['final_response'] = final_response
        logger.info(f"Generated final response: {final_response}")
        
        return {'status': 'completed', 'context': context}
    
    def _generate_final_response(self, llm_response: str, tool_result: dict, retrieved_docs: list) -> str:
        """生成完整的中医问诊回复"""
        
        # 解析LLM返回的JSON症状信息
        import json
        import re
        symptoms_data = {}
        if llm_response:
            json_match = re.search(r'```json\s*(.*?)\s*```', llm_response, re.DOTALL)
            if json_match:
                try:
                    symptoms_data = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
        
        # 提取辨证结果
        syndrome = tool_result.get('syndrome', '')
        syndrome_desc = tool_result.get('description', '')
        
        # 提取方剂推荐
        prescriptions = tool_result.get('prescriptions', [])
        
        # 构建完整回复
        response_parts = []
        
        # 1. 问候和症状总结
        response_parts.append("您好！根据您的描述，我已为您进行了中医问诊分析，结果如下：")
        
        # 2. 症状提取结果
        # 支持中英文键名
        main_symptoms = symptoms_data.get('main_symptoms') or symptoms_data.get('主要症状', '')
        accompanying_symptoms = symptoms_data.get('accompanying_symptoms') or symptoms_data.get('伴随症状', '')
        tongue_coating = symptoms_data.get('tongue_coating') or symptoms_data.get('舌苔情况', '')
        pulse_condition = symptoms_data.get('pulse_condition') or symptoms_data.get('脉象情况', '')
        
        # 确保症状数据是可迭代的
        if not isinstance(main_symptoms, list):
            main_symptoms = [main_symptoms] if main_symptoms else []
        if not isinstance(accompanying_symptoms, list):
            accompanying_symptoms = [accompanying_symptoms] if accompanying_symptoms else []
        
        # 过滤掉空字符串
        main_symptoms = [symptom for symptom in main_symptoms if symptom.strip()]
        accompanying_symptoms = [symptom for symptom in accompanying_symptoms if symptom.strip()]
        
        has_symptoms = any([main_symptoms, accompanying_symptoms, tongue_coating, pulse_condition])
        if has_symptoms:
            response_parts.append("\n症状分析：")
            if main_symptoms:
                response_parts.append(f"- 主要症状：{', '.join(main_symptoms)}")
            if accompanying_symptoms:
                response_parts.append(f"- 伴随症状：{', '.join(accompanying_symptoms)}")
            if tongue_coating:
                response_parts.append(f"- 舌苔情况：{tongue_coating}")
            if pulse_condition:
                response_parts.append(f"- 脉象情况：{pulse_condition}")
        
        # 3. 辨证结果
        if syndrome or syndrome_desc:
            response_parts.append("\n辨证结果：")
            response_parts.append(f"- 证型：{syndrome}")
            response_parts.append(f"- 分析：{syndrome_desc}")
        
        # 4. 方剂推荐
        if prescriptions:
            response_parts.append("\n方剂推荐：")
            for i, prescription in enumerate(prescriptions, 1):
                response_parts.append(f"\n{i}. {prescription['name']}")
                response_parts.append(f"   组成：{', '.join(prescription['ingredients'])}")
                response_parts.append(f"   用法：{prescription['usage']}")
                response_parts.append(f"   用量：{prescription['dosage']}")
        
        # 5. 温馨提示
        response_parts.append("\n温馨提示：")
        response_parts.append("- 以上分析仅供参考，请结合临床实际情况使用")
        response_parts.append("- 如有不适，请及时就医")
        response_parts.append("- 用药请在中医师指导下进行")
        
        return '\n'.join(response_parts)
    
    def validate(self) -> bool:
        return True

NODE_TYPE_MAP = {
    'start': StartNode,
    'llm': LLMNode,
    'knowledge_retrieval': KnowledgeRetrievalNode,
    'tool_call': ToolCallNode,
    'end': EndNode
}

def create_node(node_id: str, node_data: Dict[str, Any]) -> IStepNode:
    node_type = node_data.get('type', 'llm')
    node_class = NODE_TYPE_MAP.get(node_type)
    if not node_class:
        raise ValueError(f"Unknown node type: {node_type}")
    return node_class(node_id, node_data)
