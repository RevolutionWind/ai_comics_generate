import re
import json

def clean_json_string(json_str: str) -> str:
    """
    清理JSON字符串中的Markdown代码块标记和多余字符
    处理以下情况：
    1. 去除包裹JSON的```json和```标记
    2. 处理可能存在的多余换行和空格
    3. 保留合法的JSON格式内容
    4. 处理包含多个JSON数组和说明文本的复杂响应
    
    :param json_str: 包含可能污染字符的原始JSON字符串
    :return: 清理后的纯净JSON字符串
    """
    # 去除首尾空白字符
    cleaned = json_str.strip()
    
    # 去除开头的```json标记（支持带换行和不带换行的情况）
    if cleaned.startswith('```json'):
        cleaned = cleaned[6:].lstrip('\n')
    
    # 去除结尾的```标记
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3].rstrip('\n')
    
    # 处理可能残留的头部```（非json标记的情况）
    cleaned = re.sub(r'^```+', '', cleaned)
    
    # 查找所有JSON数组
    json_arrays = re.findall(r'\[[\s\S]*?\]', cleaned)
    
    if not json_arrays:
        raise ValueError("未找到有效的JSON数组")
    
    # 尝试解析每个JSON数组
    valid_arrays = []
    for array_str in json_arrays:
        try:
            # 验证是否为有效的JSON
            json.loads(array_str)
            valid_arrays.append(array_str)
        except json.JSONDecodeError:
            continue
    
    if not valid_arrays:
        raise ValueError("未找到有效的JSON数组")
    
    # 返回最后一个有效的JSON数组（通常是熔断后的结果）
    return valid_arrays[-1].strip()

