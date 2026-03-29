from typing import Dict, Any, List
from datetime import datetime
from apps.application.flow.i_step_node import create_node
from apps.application.models import WorkflowNode, WorkflowEdge, Application

class WorkflowManager:
    
    def __init__(self, application_id: str):
        self.application_id = application_id
        self.nodes = {}
        self.edges = []
        self._load_workflow()
    
    def _load_workflow(self):
        from apps.application.models import Application
        import json
        
        # 尝试从WorkflowNode和WorkflowEdge表中加载工作流
        nodes = WorkflowNode.objects.filter(application_id=self.application_id, is_delete=False)
        edges = WorkflowEdge.objects.filter(application_id=self.application_id, is_delete=False)
        
        # 如果有节点，就使用表中的数据
        if nodes:
            for node in nodes:
                self.nodes[node.node_id] = {
                    'data': node.node_data,
                    'position': node.position
                }
            
            for edge in edges:
                self.edges.append({
                    'source': edge.source_node,
                    'target': edge.target_node,
                    'data': edge.edge_data
                })
        else:
            # 否则，从应用的work_flow字段中加载工作流
            try:
                application = Application.objects.get(id=self.application_id)
                work_flow = json.loads(application.work_flow)
                
                # 加载节点
                for node in work_flow.get('nodes', []):
                    self.nodes[node['id']] = {
                        'data': {
                            'type': node['type'],
                            **node['data']
                        },
                        'position': node['position']
                    }
                
                # 加载边
                for edge in work_flow.get('edges', []):
                    self.edges.append({
                        'source': edge['source'],
                        'target': edge['target'],
                        'data': edge['data']
                    })
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to load workflow from application.work_flow: {str(e)}", exc_info=True)
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        import logging
        
        # 设置日志记录
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        
        try:
            context = input_data.copy()
            logger.info(f"Starting workflow execution with input_data: {input_data}")
            
            start_node = self._find_start_node()
            
            if not start_node:
                logger.error("No start node found in workflow")
                return {'status': 'error', 'message': 'No start node found'}
            
            logger.info(f"Found start node: {start_node['node_id']}")
            current_node_id = start_node['node_id']
            visited_nodes = set()
            
            while current_node_id and current_node_id not in visited_nodes:
                visited_nodes.add(current_node_id)
                logger.info(f"Processing node: {current_node_id}")
                
                node_data = self.nodes.get(current_node_id)
                if not node_data:
                    logger.error(f"Node data not found for node_id: {current_node_id}")
                    break
                
                logger.info(f"Creating node with data: {node_data['data']}")
                node = create_node(current_node_id, node_data['data'])
                
                if not node.validate():
                    logger.error(f"Node validation failed for node_id: {current_node_id}")
                    return {'status': 'error', 'message': f'Node {current_node_id} validation failed'}
                
                result = node.execute(context)
                logger.info(f"Node execution result: {result}")
                
                # 检查节点执行结果，end节点返回的是completed状态
                if result['status'] not in ['success', 'completed']:
                    logger.error(f"Node execution failed for node_id: {current_node_id}, result: {result}")
                    return result
                
                context = result['context']
                logger.info(f"Updated context: {context}")
                
                if result['status'] == 'completed':
                    # 这是end节点，直接返回结果
                    logger.info(f"Reached end node: {current_node_id}")
                    return result
                
                current_node_id = self._get_next_node(current_node_id)
                logger.info(f"Next node: {current_node_id}")
            
            logger.error("Workflow execution incomplete, reached end of nodes without finding end node")
            return {'status': 'error', 'message': 'Workflow execution incomplete'}
        except Exception as e:
            logger.error(f"Unexpected error in workflow execution: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': f'Workflow execution failed: {str(e)}'}
    
    def _find_start_node(self) -> Dict[str, Any]:
        for node_id, node_data in self.nodes.items():
            if node_data['data'].get('type') == 'start':
                return {'node_id': node_id, 'data': node_data}
        return None
    
    def _get_next_node(self, current_node_id: str) -> str:
        for edge in self.edges:
            if edge['source'] == current_node_id:
                return edge['target']
        return None
    
    def validate_workflow(self) -> Dict[str, Any]:
        errors = []
        
        if not self._find_start_node():
            errors.append('No start node found')
        
        has_end_node = any(
            node_data['data'].get('type') == 'end'
            for node_data in self.nodes.values()
        )
        
        if not has_end_node:
            errors.append('No end node found')
        
        for edge in self.edges:
            if edge['source'] not in self.nodes:
                errors.append(f"Edge source node {edge['source']} not found")
            if edge['target'] not in self.nodes:
                errors.append(f"Edge target node {edge['target']} not found")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

class TCMWorkflowManager(WorkflowManager):
    
    def execute_diagnosis_workflow(self, symptoms: List[str]) -> Dict[str, Any]:
        input_data = {
            'user_query': f'症状：{", ".join(symptoms)}',
            'symptoms': symptoms,
            'task_type': 'diagnosis'
        }
        return self.execute(input_data)
    
    def execute_prescription_workflow(self, syndrome: str) -> Dict[str, Any]:
        input_data = {
            'user_query': f'证型：{syndrome}',
            'syndrome': syndrome,
            'task_type': 'prescription'
        }
        return self.execute(input_data)
    
    def execute_classic_search_workflow(self, keyword: str) -> Dict[str, Any]:
        input_data = {
            'user_query': f'古籍检索：{keyword}',
            'keyword': keyword,
            'task_type': 'classic_search'
        }
        return self.execute(input_data)
