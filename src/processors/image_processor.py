import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import uuid
import requests
from concurrent.futures import ThreadPoolExecutor

from src.config import settings
from src.utils.logger import log
from src.processors.api_client import APIClient

class ImageProcessor:
    def __init__(self):
        self.api_client = APIClient()
        
    async def _wait_for_image_completion(self, generate_uuid: str, params: Dict) -> Optional[Dict]:
        """等待生图任务完成并获取结果"""
        max_retries = 60  # 最多等待5分钟
        retry_interval = 5  # 每5秒查询一次
        
        for _ in range(max_retries):
            status = await self.api_client.query_image_status(generate_uuid, params)
            if not status:
                await asyncio.sleep(retry_interval)
                continue
                
            if status.get("status") == "SUCCESS":
                return status
            elif status.get("status") == "FAILED":
                raise Exception(f"生图任务失败: {status}")
                
            await asyncio.sleep(retry_interval)
            
        raise Exception("生图任务超时")

    async def generate_image(self, prompt: Dict, copy_id: str, topic_id: str, event_id: str) -> Dict:
        """使用Liblib API生成图片"""
        log.info(f"[Event:{event_id}][Topic:{topic_id}][Copy:{copy_id}][Prompt:{prompt['id']}] 开始生成图片")
        
        try:
            # 准备请求参数
            params = {
                "AccessKey": settings.SD_ACCESS_KEY,
                "templateUuid": settings.SD_TEMPLATE_UUID
            }
            
            # 提交生图任务
            generate_uuid = await self.api_client.submit_image_task(prompt, params)
            log.info(f"提交生图任务结果 generate_uuid: {generate_uuid}")
            
            if not generate_uuid:
                raise Exception("提交生图任务失败")
                
            # 等待任务完成
            result = await self._wait_for_image_completion(generate_uuid, params)
            
            # 保存图片
            if result.get("status") != "SUCCESS":
                raise Exception(f"生图任务未成功完成，最终状态: {result.get('status')}")
            
            image_data = result.get("image_data")
            if not image_data:
                raise Exception("生图结果中没有有效的图片数据，可能未通过审核")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_id = str(uuid.uuid4())
            
            # 确保图片保存目录存在
            settings.TODAY_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
            image_path = settings.TODAY_IMAGES_DIR / f"{prompt['copy']}_image_{image_id}.png"
            
            # 下载并保存图片
            response = requests.get(image_data["url"])
            response.raise_for_status()
            
            with open(image_path, "wb") as f:
                f.write(response.content)
                
            result = {
                "id": image_id,
                "path": str(image_path),
                "seed": image_data.get("seed")
            }
            
            log.info(f"[Event:{event_id}][Topic:{topic_id}][Copy:{copy_id}][Prompt:{prompt['id']}] 成功生成图片: {result}")
            return result
            
        except Exception as e:
            log.error(f"[Event:{event_id}][Topic:{topic_id}][Copy:{copy_id}][Prompt:{prompt['id']}] 生成图片失败: {str(e)}")
            raise

    # def generate_image_sync(self, prompt: Dict, copy_id: str, topic_id: str, event_id: str) -> Dict:
    #     """同步版本的图片生成方法"""
    #     loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop)
    #     try:
    #         return loop.run_until_complete(self.generate_image(prompt, copy_id, topic_id, event_id))
    #     finally:
    #         loop.close()

    async def generate_images_batch(self, prompts: List[Dict], copy_id: str, topic_id: str, event_id: str) -> List[Dict]:
        """批量生成图片（多线程版本）"""
        log.info(f"[Event:{event_id}][Topic:{topic_id}][Copy:{copy_id}] 开始批量生成图片，共 {len(prompts)} 个任务")
        
        # 单线程顺序执行生成任务
        results = []
        for prompt in prompts:
            try:
                result = await self.generate_image(prompt, copy_id, topic_id, event_id)
                results.append(result)
            except Exception as e:
                log.error(f"任务执行失败: {str(e)}")
                results.append(e)

        # 处理结果
        successful_results = []
        for result in results:
            if isinstance(result, Exception):
                log.error(f"任务执行失败: {str(result)}")
                continue
            successful_results.append(result)
            
        log.info(f"[Event:{event_id}][Topic:{topic_id}][Copy:{copy_id}] 批量生图完成，成功: {len(successful_results)}/{len(prompts)}")
        return successful_results
    
if __name__ == "__main__":
    async def main():
        try:
            image_processor = ImageProcessor()
            
            # 创建测试用的提示词列表
            test_prompts = [
                {
                    'id': 'test_prompt_1',
                    'copy': 'test1',
                    'content': 'A hand-drawn watercolor illustration with bold black outlines in a minimalist, cartoon-like style. The image shows a 【person description: bald person with closed eyes and rosy cheeks】 being examined by a large 【examining object: microscope】. The 【examining object】 has a blue-gray color and extends a curved arm holding a small 【held item: beige sack with Chinese character】. The 【person】 is wearing a 【clothing: simple white robe】 and displays a 【emotion: nervous】 expression.'
                },
                {
                    'id': 'test_prompt_2', 
                    'copy': 'test2',
                    'content': 'A minimalist watercolor painting in soft pastel colors showing a 【object: vintage camera】 sitting on a 【surface: wooden table】. The camera has 【details: brass accents and leather straps】 with a 【background: blurred bookshelf】. The style features loose brushstrokes and subtle texture effects.'
                }
            ]
            
            # 测试批量生成方法
            results = await image_processor.generate_images_batch(
                prompts=test_prompts,
                copy_id='test_copy_id',
                topic_id='test_topic_id',
                event_id='test_event_id'
            )
            
            print('批量生成结果:')
            for i, result in enumerate(results, 1):
                print(f'图片{i}: {result}')
                
        except Exception as e:
            import traceback
            print(f"批量生成测试失败: {str(e)}")
            print(traceback.format_exc())
    
    # 运行异步主函数
    asyncio.run(main())