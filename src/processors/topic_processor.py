import json
import uuid
from typing import List, Dict

from src.config import settings
from src.utils.logger import log
from src.processors.api_client import APIClient
from src.utils.json_util import clean_json_string

class TopicProcessor:
    def __init__(self):
        self.api_client = APIClient()
        
    async def extract_topics(self, event_description: str, event_id: str) -> List[Dict]:
        """从事件描述中提取主题"""
        log.info(f"[Event:{event_id}] 开始从事件中提取主题: {event_description}")
        
        prompt = settings.TOPIC_EXTRACTION_PROMPT.format(
            topic_count=settings.TOPICS_PER_EVENT,
            event_description=event_description
        )
        
        try:
            content = await self.api_client.call_deepseek_api([
                {"role": "user", "content": prompt}
            ])

            content = clean_json_string(content)

            topics = json.loads(content)
            # 为每个主题添加ID
            topics_with_id = [
                {"id": str(uuid.uuid4()), "content": topic}
                for topic in topics
            ]
            log.info(f"[Event:{event_id}] 成功提取主题: {topics_with_id}")
            return topics_with_id
        except Exception as e:
            log.error(f"[Event:{event_id}] 提取主题失败: {str(e)}")
            raise 