from typing import Dict, Any, List

class TCMTools:
    
    def __init__(self):
        self.tools = {
            'diagnosis': self._diagnosis_tool,
            'prescription_search': self._prescription_search_tool,
            'herb_query': self._herb_query_tool,
            'classic_search': self._classic_search_tool,
            'contraindication_check': self._contraindication_check_tool
        }
    
    def call(self, tool_name: str, params: Dict[str, Any]) -> Any:
        tool_func = self.tools.get(tool_name)
        if not tool_func:
            raise ValueError(f"Tool {tool_name} not found")
        return tool_func(params)
    
    def _diagnosis_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        symptoms = params.get('symptoms', [])
        
        diagnosis_rules = {
            '风寒感冒': ['怕冷', '流清涕', '无汗', '脉浮紧'],
            '风热感冒': ['发热', '咽痛', '流黄涕', '脉浮数'],
            '湿热证': ['舌苔黄腻', '口苦', '小便短赤', '脉滑数'],
            '寒湿证': ['舌苔白腻', '口淡', '小便清长', '脉濡缓']
        }
        
        matched_syndrome = None
        max_match = 0
        
        for syndrome, required_symptoms in diagnosis_rules.items():
            match_count = len(set(symptoms) & set(required_symptoms))
            if match_count > max_match:
                max_match = match_count
                matched_syndrome = syndrome
        
        return {
            'syndrome': matched_syndrome,
            'confidence': max_match / len(symptoms) if symptoms else 0,
            'matched_symptoms': max_match
        }
    
    def _prescription_search_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        syndrome = params.get('syndrome', '')
        
        prescriptions = {
            '风寒感冒': [
                {'name': '桂枝汤', 'herbs': ['桂枝', '芍药', '甘草', '生姜', '大枣']},
                {'name': '麻黄汤', 'herbs': ['麻黄', '桂枝', '杏仁', '甘草']}
            ],
            '风热感冒': [
                {'name': '银翘散', 'herbs': ['金银花', '连翘', '薄荷', '荆芥', '淡豆豉']},
                {'name': '桑菊饮', 'herbs': ['桑叶', '菊花', '杏仁', '连翘', '薄荷']}
            ],
            '湿热证': [
                {'name': '三仁汤', 'herbs': ['杏仁', '白蔻仁', '薏苡仁', '滑石', '通草']},
                {'name': '甘露消毒丹', 'herbs': ['滑石', '茵陈', '黄芩', '石菖蒲']}
            ]
        }
        
        return {
            'syndrome': syndrome,
            'prescriptions': prescriptions.get(syndrome, [])
        }
    
    def _herb_query_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        herb_name = params.get('herb_name', '')
        
        herbs = {
            '麻黄': {
                'efficacy': '发汗解表，宣肺平喘，利水消肿',
                'contraindications': '体虚自汗、肺肾虚咳者禁用',
                'dosage': '2-9g'
            },
            '桂枝': {
                'efficacy': '发汗解肌，温通经脉，助阳化气',
                'contraindications': '热证、阴虚火旺者慎用',
                'dosage': '3-9g'
            },
            '金银花': {
                'efficacy': '清热解毒，疏散风热',
                'contraindications': '脾胃虚寒者不宜大量使用',
                'dosage': '6-15g'
            },
            '连翘': {
                'efficacy': '清热解毒，消肿散结',
                'contraindications': '脾胃虚寒者慎用',
                'dosage': '6-15g'
            }
        }
        
        return herbs.get(herb_name, {'message': f'未找到药材 {herb_name} 的信息'})
    
    def _classic_search_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        keyword = params.get('keyword', '')
        
        classics = {
            '桂枝汤': {
                'source': '伤寒论',
                'content': '太阳中风，阳浮而阴弱，阳浮者，热自发；阴弱者，汗自出。啬啬恶寒，淅淅恶风，翕翕发热，鼻鸣干呕者，桂枝汤主之。',
                'application': '用于风寒感冒，营卫不和证'
            },
            '麻黄汤': {
                'source': '伤寒论',
                'content': '太阳病，头痛发热，身疼腰痛，骨节疼痛，恶风，无汗而喘者，麻黄汤主之。',
                'application': '用于风寒感冒，表实证'
            },
            '银翘散': {
                'source': '温病条辨',
                'content': '太阴风温、温热、温疫、冬温，初起恶风寒者，桂枝汤主之；但发热不恶寒而渴者，辛凉平剂银翘散主之。',
                'application': '用于风热感冒，温病初起'
            }
        }
        
        results = []
        for name, info in classics.items():
            if keyword in name or keyword in info['content']:
                results.append({
                    'name': name,
                    'source': info['source'],
                    'content': info['content'],
                    'application': info['application']
                })
        
        return {'keyword': keyword, 'results': results}
    
    def _contraindication_check_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        herbs = params.get('herbs', [])
        
        incompatibilities = {
            '甘草': ['甘遂', '大戟', '芫花', '海藻'],
            '乌头': ['半夏', '瓜蒌', '贝母', '白蔹', '白及'],
            '藜芦': ['人参', '沙参', '丹参', '玄参', '苦参', '细辛', '芍药']
        }
        
        conflicts = []
        for herb in herbs:
            if herb in incompatibilities:
                for incompatible_herb in incompatibilities[herb]:
                    if incompatible_herb in herbs:
                        conflicts.append({
                            'herb1': herb,
                            'herb2': incompatible_herb,
                            'rule': '十八反'
                        })
        
        return {
            'herbs': herbs,
            'has_conflict': len(conflicts) > 0,
            'conflicts': conflicts,
            'is_safe': len(conflicts) == 0
        }
