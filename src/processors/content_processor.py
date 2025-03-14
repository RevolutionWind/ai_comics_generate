from typing import List, Dict
from pathlib import Path
from datetime import datetime
import uuid
from hashlib import sha1
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional
from collections import deque
import itertools

from src.config import settings
from src.utils.logger import log
from src.processors.topic_processor import TopicProcessor
from src.processors.copy_processor import CopyProcessor
from src.processors.image_processor import ImageProcessor

class ContentProcessor:
    def __init__(self):
        self.topic_processor = TopicProcessor()
        self.copy_processor = CopyProcessor()
        self.image_processor = ImageProcessor()

    async def process_event(self, event_description: str):
        """处理完整的事件流程
        Args:
            event_description: 事件描述文本
        Returns:
            list: 包含所有生成结果的列表，每个元素包含主题、文案、提示词和图片信息
        """
        event_id = str(uuid.uuid4())
        log.info(f"[Event:{event_id}] 开始处理新事件: {event_description}")
        
        try:
            # 第一阶段：提取主题和生成文案
            topics = await self._extract_topics(event_description, event_id)
            all_copies = await self._generate_all_copies(topics, event_id)
            
            # 第二阶段：生成图片提示词
            prompts_by_copy = await self._generate_all_prompts(topics, all_copies, event_id)
            
            # 第三阶段：批量生成图片
            results = await self._process_image_batches(topics, all_copies, prompts_by_copy, event_id)
            
            log.info(f"[Event:{event_id}] 事件处理完成")
            return results
        except Exception as e:
            log.error(f"[Event:{event_id}] 事件处理失败: {str(e)}")
            raise

    async def _extract_topics(self, event_description: str, event_id: str) -> list:
        """提取事件中的主题"""
        log.debug(f"[Event:{event_id}] 开始提取主题")
        return await self.topic_processor.extract_topics(event_description, event_id)

    def _run_async_task(self, coroutine_func, *args):
        """在同步线程中运行异步任务的通用方法"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coroutine_func(*args))
        finally:
            loop.close()

    async def _generate_all_copies(self, topics: list, event_id: str) -> list:
        """并行生成所有主题的文案"""
        log.debug(f"[Event:{event_id}] 开始生成文案")
        
        with ThreadPoolExecutor() as executor:
            # 为每个主题创建文案生成任务
            tasks = [
                executor.submit(self._run_async_task, self.copy_processor.generate_copies, topic, event_id)
                for topic in topics
            ]
            
            # 收集并处理结果
            return self._collect_results(tasks, f"[Event:{event_id}] 生成文案失败")

    async def _generate_all_prompts(self, topics: list, all_copies: list, event_id: str) -> dict:
        """生成所有文案对应的图片提示词"""
        log.debug(f"[Event:{event_id}] 开始生成图片提示词")
        prompts_by_copy = {}
        
        # 为每个文案创建提示词生成任务
        for topic_idx, copies in enumerate(all_copies):
            for copy in copies:
                try:
                    # 直接使用await调用异步方法
                    result = await self.copy_processor.generate_image_prompts(
                        copy,
                        topics[topic_idx]['id'],
                        event_id
                    )
                    prompts_by_copy[copy['id']] = deque(result)
                except Exception as e:
                    log.error(f"[Event:{event_id}][Copy:{copy['id']}] 生成提示词失败: {str(e)}")
                    prompts_by_copy[copy['id']] = deque()
        return prompts_by_copy

    async def _process_image_batches(self, topics: list, all_copies: list, prompts_by_copy: dict, event_id: str) -> list:
        """批量处理图片生成任务"""
        log.debug(f"[Event:{event_id}] 开始处理图片生成")
        results = []
        
        batch = []
        # 遍历所有主题和文案组合
        for topic_idx, (topic, copies) in enumerate(zip(topics, all_copies)):
            for copy_idx, copy in enumerate(copies):
                # 准备图片生成参数
                copy_prompts = self._prepare_prompts(copy, prompts_by_copy, event_id, topic)
                batch.append((copy, topic, copy_prompts))
                
                # 立即提交当前任务（单线程模式）
                results.extend(await self._process_batch_async(batch, event_id))
                batch = []
        return results

    def _prepare_prompts(self, copy: dict, prompts_by_copy: dict, event_id: str, topic: dict) -> list:
        """准备图片生成所需的提示词"""
        prompts = list(itertools.islice(prompts_by_copy[copy['id']], 0, settings.SD_PROMPT_PER_COPY))
        if len(prompts) < settings.SD_PROMPT_PER_COPY:
            log.warning(f"[Event:{event_id}][Topic:{topic['id']}][Copy:{copy['id']}] 提示词不足: 需要{settings.SD_PROMPT_PER_COPY}个，实际得到{len(prompts)}个")
        return prompts

    def _is_last_item(self, topic_idx: int, copy_idx: int, topics: list, copies: list) -> bool:
        """判断是否是最后一个处理项"""
        return copy_idx == len(copies)-1 and topic_idx == len(topics)-1

    def _submit_batch(self, executor: ThreadPoolExecutor, batch: list, event_id: str) -> list:
        """提交并处理单个批任务"""
        future = executor.submit(self._process_batch_sync, batch=batch, event_id=event_id)
        try:
            return future.result()
        except Exception as e:
            log.error(f"批处理任务执行失败: {str(e)}")
            return []

    def _collect_results(self, tasks: list, error_msg: str) -> list:
        """通用结果收集方法"""
        results = []
        for task in tasks:
            try:
                results.append(task.result())
            except Exception as e:
                log.error(f"{error_msg}: {str(e)}")
                continue
        return results

    def _process_batch_sync(self, batch: list, event_id: str) -> list:
        """同步处理批任务"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self._process_batch_async(batch, event_id))
        finally:
            loop.close()

    async def _process_batch_async(self, batch: list, event_id: str) -> list:
        """异步处理单个批次"""
        batch_results = []
        tasks = [
            self.image_processor.generate_images_batch(
                prompts=item[2],  # copy_prompts
                copy_id=item[0]['id'],
                topic_id=item[1]['id'],
                event_id=event_id
            )
            for item in batch
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (copy, topic, copy_prompts), images in zip(batch, results):
            if isinstance(images, Exception):
                log.error(f"[Event:{event_id}][Topic:{topic['id']}][Copy:{copy['id']}] 图片生成失败: {str(images)}")
                continue
                
            batch_results.append({
                "event_id": event_id,
                "topic": topic,
                "copy": copy,
                "prompts": copy_prompts,
                "images": images
            })
    
        return batch_results
            