# AI 漫画生成器

这是一个自动化的 AI 内容生成系统，可以将文字描述转换为漫画图片。系统包含以下功能：

1. 主题提取：从输入的事件描述中提取多个有趣的主题
2. 文案生成：为每个主题生成多个生动的文案
3. 提示词生成：将文案转换为 Stable Diffusion 可用的图片生成提示词
4. 图片生成：调用 Stable Diffusion API 生成漫画风格的图片

## 环境要求

- Python 3.10
- OpenAI API 密钥
- Liblib API AccessKey
- Liblib API SecretKey

## 安装

1. 克隆仓库：

```bash
git clone [repository_url]
cd ai_comics_generate
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 执行安装命令：

```bash
pip install -e .
```

4. 配置环境变量：
   config.py

```
OPENAI_API_KEY=你的OpenAI API密钥
SD_ACCESS_KEY=你的Liblib API AccessKey
SD_SECRET_KEY=你的Liblib API SecretKey
SD_TEMPLATE_UUID=你的Liblib API TemplateUUID
```

## 使用方法

1. 直接运行示例：

```bash
python -m src.processors.content_processor
```

2. 在代码中使用：

```python
from src.processors.content_processor import main
import asyncio

event_description = "你的事件描述"
results = asyncio.run(main(event_description))
```

## 输出说明

- 生成的图片保存在 `output/images/[日期]/` 目录下
- 处理日志保存在 `output/logs/[日期]/` 目录下
- 每次处理的详细结果以 JSON 格式保存在日志目录中

## 配置说明

可以在 `src/config.py` 中修改以下配置：

- `TOPICS_PER_EVENT`: 每个事件提取的主题数量
- `COPIES_PER_TOPIC`: 每个主题生成的文案数量
- `IMAGES_PER_COPY`: 每个文案生成的图片数量
