import asyncio
from pathlib import Path
import json
from datetime import datetime

from .processors.content_processor import ContentProcessor
from .utils.logger import log
from .config import settings

async def main(event_description: str):
    """
    主程序入口
    
    Args:
        event_description: 事件描述文本
    """
    processor = ContentProcessor()
    
    try:
        # 处理事件并获取结果
        results = await processor.process_event(event_description)
        
        # 保存处理结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = settings.TODAY_LOGS_DIR / f"result_{timestamp}.json"
        
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        log.info(f"结果已保存到: {result_file}")
        return results
        
    except Exception as e:
        log.error(f"处理失败: {str(e)}")
        raise

if __name__ == "__main__":
    # 示例使用
    event_description = """
    在一个阳光明媚的下午，小明在公园里遇到了一只会说话的松鼠，
    它告诉小明自己是来自未来的时空旅行者，需要完成一项拯救地球的任务。
    """
    
    asyncio.run(main(event_description)) 