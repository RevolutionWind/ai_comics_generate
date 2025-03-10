import requests
import hmac
import base64
from hashlib import sha1
import uuid
import time
from typing import List, Dict, Optional

from src.config import settings
from src.utils.logger import log

class APIClient:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE

    async def call_deepseek_api(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """调用 Deepseek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": settings.deepseek_LLM_MODEL,
            "messages": messages,
            "temperature": temperature
        }
        
        try:
            response = requests.post(
                f"{self.api_base}{settings.DEEPSEEK_CHAT_COMPLETIONS}",
                headers=headers,
                json=data
            )

            log.info(f"Deepseek API 响应: {response.json()}")
            
            if response.status_code != 200:
                raise Exception(f"Deepseek API 请求失败: {response.text}")
                
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            log.error(f"Deepseek API 调用失败: {str(e)}")
            raise
    
    async def call_claude_api(self, messages: List[Dict], system: str = None, temperature: float = 0.7) -> str:
        """调用 Claude API (通过 OpenRouter)"""
        try:
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }

            # 转换消息格式
            formatted_messages = []
            for msg in messages:
                content = []
                if isinstance(msg["content"], str):
                    content = [{"type": "text", "text": msg["content"]}]
                elif isinstance(msg["content"], list):
                    content = msg["content"]
                formatted_messages.append({"role": msg["role"], "content": content})

            # 如果有系统提示，添加到消息列表开头
            if system:
                formatted_messages.insert(0, {
                    "role": "system",
                    "content": [{"type": "text", "text": system}]
                })

            data = {
                "model": settings.CLAUDE_MODEL,
                "messages": formatted_messages
            }

            response = requests.post(
                settings.OPENROUTER_API_URL,
                headers=headers,
                json=data
            )

            if response.status_code != 200:
                raise Exception(f"OpenRouter API 请求失败: {response.text}")

            log.info(f"OpenRouter API 响应: {response.json()}")
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            log.error(f"OpenRouter API 调用失败: {str(e)}")
            raise

    async def _generate_signature(self, uri: str, timestamp: str, signature_nonce: str) -> str:
        """生成API签名"""
        content = '&'.join((uri, timestamp, signature_nonce))
        digest = hmac.new(settings.SD_SECRET_KEY.encode(), content.encode(), sha1).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b'=').decode()

    async def query_image_status(self, generate_uuid: str, params: Dict) -> Optional[Dict]:
        """查询生图任务状态
        返回格式:
        {
            "status": "PENDING|PROCESSING|GENERATED|AUDITING|SUCCESS|FAILED|TIMEOUT",
            "message": str,         # 状态信息
            "percent": float,       # 完成百分比（0-1）
            "cost": int,            # 消耗点数
            "balance": int,         # 账户余额
            "image_data": Optional[Dict]  # 图片数据 {url: str, seed: int}
        }
        """
        try:
            timestamp = str(int(time.time() * 1000))
            signature_nonce = str(uuid.uuid4())
            uri = settings.SD_API_URL_STATUS
            
            signature = await self._generate_signature(uri, timestamp, signature_nonce)
            
            headers = {"Content-Type": "application/json"}
            query_params = {
                "AccessKey": settings.SD_ACCESS_KEY,
                "Signature": signature,
                "Timestamp": timestamp,
                "SignatureNonce": signature_nonce
            }
            data = {"generateUuid": generate_uuid}
            
            response = requests.post(
                f"{settings.SD_API_URL}{settings.SD_API_URL_STATUS}",
                headers=headers,
                params=query_params,
                json=data
            )

            log.info(f"查询生图状态API 响应: {response.json()}")
            
            if response.status_code != 200:
                raise Exception(f"查询状态API请求失败: {response.text}")
                
            resp_data = response.json().get("data", {})
            
            # 映射状态码到文字
            status_mapping = {
                1: "PENDING",
                2: "PROCESSING",
                3: "GENERATED",
                4: "AUDITING",
                5: "SUCCESS",
                6: "FAILED",
                7: "TIMEOUT"
            }
            
            status_code = resp_data.get("generateStatus", 6)
            status = status_mapping.get(status_code, "FAILED")
            
            # 提取审核通过的图片数据（auditStatus=3）
            image_data = None
            if resp_data.get("images"):
                valid_images = [img for img in resp_data["images"] if img.get("auditStatus") == 3]
                if valid_images:
                    first_image = valid_images[0]
                    image_data = {
                        "url": first_image.get("imageUrl"),
                        "seed": first_image.get("seed")
                    }
            
            return {
                "status": status,
                "message": resp_data.get("generateMsg", ""),
                "percent": resp_data.get("percentCompleted", 0.0),
                "cost": resp_data.get("pointsCost", 0),
                "balance": resp_data.get("accountBalance", 0),
                "image_data": image_data
            }
            
        except Exception as e:
            log.error(f"查询生图状态失败: {str(e)}")
            return None

    async def submit_image_task(self, prompt: Dict, params: Dict) -> Optional[str]:
        """提交生图任务"""
        try:
            timestamp = str(int(time.time() * 1000))
            signature_nonce = str(uuid.uuid4())
            uri = settings.SD_API_URL_TEXT2IMG
            
            signature = await self._generate_signature(uri, timestamp, signature_nonce)
            
            headers = {"Content-Type": "application/json"}
            
            query_params = {
                "AccessKey": settings.SD_ACCESS_KEY,
                "Signature": signature,
                "Timestamp": timestamp,
                "SignatureNonce": signature_nonce
            }
            
            data = {
                "templateUuid": settings.SD_TEMPLATE_UUID,
                "generateParams": {
                    "prompt": prompt['content'],
                    "steps": 20,
                    "width": 1024,
                    "height": 1024,
                    "imgCount": settings.IMAGE_PER_PROMPT,
                    "seed": -1,
                    "restoreFaces": 0
                }
            }
            
            response = requests.post(
                f"{settings.SD_API_URL}{settings.SD_API_URL_TEXT2IMG}",
                headers=headers,
                params=query_params,
                json=data
            )

            if response.status_code != 200:
                raise Exception(f"提交任务API请求失败: {response.text}")
                
            result = response.json()
            if result.get("code") == 0 and "data" in result and "generateUuid" in result["data"]:
                return result["data"]["generateUuid"]
            else:
                log.error(f"提交任务API响应格式不正确: {result}")
                return None
            
        except Exception as e:
            log.error(f"提交生图任务失败: {str(e)}")
            return None 