# 中医智能问诊系统提示词模板
# 根据实际字段完善，用于调用大模型

# 定义完整的提示词模板，包含所有实际可用的字段
CHAT_PROMPT_TEMPLATES = {
    'DEFAULT': """{system_prompt}

    历史聊天记录：
    {history}

    可参考的上下文：
    {context}

    {files}

    问题：{question}

    请基于以上信息回答用户的问题。如果你不知道答案，就说你不知道。总是使用中文回答。
    请直接回答问题，不要使用'根据提供的信息'、'支撑信息显示'等前缀。""",
    
    'RAG_TEMPLATE': """{system_prompt}

    历史聊天记录：
    {history}

    可参考的上下文：
    ···
    {context}
    ···

    {files}

    问题：{question}

    使用以上上下文来回答用户的问题。如果你不知道答案，就说你不知道。总是使用中文回答。
    如果给定的上下文无法让你做出回答，请回答数据库中没有这个内容，你不知道。""",
    
    'TCM_DIAGNOSIS_TEMPLATE': """{system_prompt}

    历史聊天记录：
    {history}

    可参考的上下文：
    {context}

    {files}

    患者症状：{question}

    请按照中医问诊的规范流程，基于以上信息进行辨证分析，并给出相应的诊断结果和治疗建议。
    回答内容应包括：
    1. 辨证分析（包括病因病机、证候判断等）
    2. 诊断结果（证型名称）
    3. 治疗建议（包括方剂、针灸、食疗等）
    4. 注意事项
    
    请使用专业的中医术语，同时确保语言通俗易懂，便于患者理解。""",
    
    'SIMPLE_TEMPLATE': """{system_prompt}

    {files}

    问题：{question}

    请直接回答用户的问题，不要使用'根据提供的信息'、'支撑信息显示'等前缀。"""
}

# 用于生成最终提示词的函数
def generate_prompt(template_type: str, system_prompt: str, question: str, context: str = "", history: str = "", files: str = "") -> str:
    """
    根据模板类型和实际字段生成最终提示词
    
    参数：
    - template_type: 模板类型，如 'DEFAULT'、'RAG_TEMPLATE' 等
    - system_prompt: 系统提示词
    - question: 用户问题
    - context: 知识库检索结果，默认为空
    - history: 历史聊天记录，默认为空
    - files: 文件信息，默认为空
    
    返回：
    - 生成的最终提示词
    """
    # 获取对应的模板
    template = CHAT_PROMPT_TEMPLATES.get(template_type, CHAT_PROMPT_TEMPLATES['DEFAULT'])
    
    # 替换模板中的占位符
    prompt = template.format(
        system_prompt=system_prompt or "",
        history=history or "",
        context=context or "",
        question=question,
        files=files or ""
    )
    
    return prompt
