import json
import uuid
import asyncio
from typing import List, Dict

from src.config import settings
from src.utils.logger import log
from src.processors.api_client import APIClient
from src.utils.json_util import clean_json_string

class CopyProcessor:
    def __init__(self):
        self.api_client = APIClient()
        
    async def generate_copies(self, topic: Dict, event_id: str) -> List[Dict]:
        """为每个主题生成文案"""
        log.info(f"[Event:{event_id}][Topic:{topic['id']}] 开始为主题生成文案: {topic['content']}")
        
        system_prompt = settings.CLAUDE_COPY_GENERATION_PROMPT.format(
            copy_count=settings.COPIES_PER_TOPIC
        )
        
        try:
            content = await self.api_client.call_claude_api([
                {"role": "user", "content": f"主题：{topic['content']}"}
            ], system=system_prompt, temperature=0.8)

            content = clean_json_string(content)
            copies = json.loads(content)
            # 为每个文案添加ID
            copies_with_id = [
                {"id": str(uuid.uuid4()), "content": copy}
                for copy in copies
            ]
            log.info(f"[Event:{event_id}][Topic:{topic['id']}] 成功生成文案: {copies_with_id}")
            return copies_with_id
        except Exception as e:
            log.error(f"[Event:{event_id}][Topic:{topic['id']}] 生成文案失败: {str(e)}")
            raise
            
    async def generate_image_prompts(self, copy: Dict, topic_id: str, event_id: str) -> List[Dict]:
        """为每个文案生成SD提示词"""
        log.info(f"[Event:{event_id}][Topic:{topic_id}][Copy:{copy['id']}] 开始生成图片提示词: {copy['content']}")
        
        prompt = settings.IMAGE_PROMPT_GENERATION_PROMPT.format(
            image_count=settings.SD_PROMPT_PER_COPY,
            copy=copy['content']
        )
        
        try:
            content = await self.api_client.call_deepseek_api([
                {"role": "user", "content": prompt}
            ], temperature=0.7)
            content = clean_json_string(content)
            prompts = json.loads(content)
            # 为每个提示词添加ID
            prompts_with_id = [
                {"id": str(uuid.uuid4()), "copy": copy['content'], "content": prompt}
                for prompt in prompts
            ]
            log.info(f"[Event:{event_id}][Topic:{topic_id}][Copy:{copy['id']}] 成功生成图片提示词: {prompts_with_id}")
            return prompts_with_id
        except Exception as e:
            log.error(f"[Event:{event_id}][Topic:{topic_id}][Copy:{copy['id']}] 生成图片提示词失败: {str(e)}")
            raise 


if __name__ == "__main__":
    async def main():
        copy_processor = CopyProcessor()
        copy = {
            "id": "test_topic_1",
            "content": "被迫准时下班：关怀政策下的新型焦虑"
        }
        topic_id = "test_topic_1"
        event_id = "test_event_1"
        result = await copy_processor.generate_copies(copy, event_id)
        print(result)

    asyncio.run(main())