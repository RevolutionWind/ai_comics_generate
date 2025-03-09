from pydantic_settings import BaseSettings
from pathlib import Path
import os
from datetime import datetime
import uuid

class Settings(BaseSettings):
    # Deepseek配置
    DEEPSEEK_API_KEY: str = "sk-259c33a9a4024f47b5badc8939cc0903"
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    DEEPSEEK_CHAT_COMPLETIONS: str = "/chat/completions"
    LLM_MODEL: str = "deepseek-reasoner"
    
    # Stable Diffusion API配置
    SD_API_URL: str = "https://openapi.liblibai.cloud"
    SD_API_URL_TEXT2IMG: str = "/api/generate/webui/text2img"
    SD_API_URL_STATUS: str = "/api/generate/webui/status"
    SD_API_KEY: str = ""
    SD_ACCESS_KEY: str = "c8ieaXRESE7IvfxBDlPiFQ"
    SD_SECRET_KEY: str = "z2Gzar_N_AvwSZCIzrgup_TuGUxCoQ_2"
    SD_TEMPLATE_UUID: str = "6f7c4652458d4802969f8d089cf5b91f"  # 参数模板ID

    # 输出配置
    OUTPUT_DIR: Path = Path("output")
    IMAGES_DIR: Path = OUTPUT_DIR / "images"
    LOGS_DIR: Path = OUTPUT_DIR / "logs"
    TODAY_IMAGES_DIR: Path = IMAGES_DIR / datetime.now().strftime("%Y%m%d")
    TODAY_LOGS_DIR: Path = LOGS_DIR / datetime.now().strftime("%Y%m%d")
    
    # 生成配置
    TOPICS_PER_EVENT: int = 3  # 每个事件生成的主题数量
    COPIES_PER_TOPIC: int = 5  # 每个主题生成的文案数量
    IMAGES_PER_COPY: int = 3   # 每个文案生成的图片数量
    
    # Prompt模板配置
    TOPIC_EXTRACTION_PROMPT: str = """
    ##角色：
    你是一位深谙人性的主题创作专家，专长于从各类背景信息中提炼出能引发强烈情感共鸣的主题，并能精准洞察当代普通人的情感需求与生活痛点。
    ##背景：
    我将提供一系列背景信息，可能涉及社会现象、人群痛点、流行趋势、节日活动或市场洞察等。这些信息可能是零散的，需要你进行整合和深入分析。
    ##目标：
    基于提供的背景信息，创造主题，这些主题需要：
    
    1. 能引发深层情感共鸣
    2. 具有独特性和创意性
    3. 能引发读者深层思考
    4. 与普通人日常生活紧密相关
    5. 具有社会传播价值
    ##技能：
    6. 精准洞察：深入理解现代人的情感需求和心理弱点（如工作压力、对未来的迷茫、对过去的怀念、社交焦虑等）
    7. 趋势把握：敏锐捕捉社会热点、季节性话题和流行趋势，提升主题时效性和传播性
    8. 情感触发：设计能唤起共情、引发思考和讨论的问题或观点
    9. 生活连接：将抽象概念或复杂背景信息转化为与普通人生活息息相关的主题
    10. 创意表达：以新颖、独特的角度呈现常见话题，避免陈词滥调
    ##流程：
    11. 全面分析所提供的背景信息，提取核心洞察和情感元素
    12. 识别目标受众可能的痛点、渴望和共鸣点
    13. 探索当前社会趋势、热点话题与背景信息的结合点
    14. 思考如何将这些元素转化为普通人易于理解且有共鸣的主题
    15. 创造能触动人心、引发深思的主题表达
    16. 为每个主题撰写简明扼要的说明，突出其情感价值和思考价值
    ##约束：
    17. 主题必须建立在提供的背景信息基础上，但需要有创造性延伸
    18. 确保内容与普通人的日常生活和情感体验高度相关
    19. 主题应具普遍性，同时保持独特视角
    20. 表达要清晰简洁，避免晦涩难懂的概念
    21. 即使探讨痛点或负面情绪，也应包含积极的思考方向或解决视角
    22. 避免过度营销化或说教式表达，保持真诚共情的语调

    请从以下事件描述中提取{topic_count}个主题：
    
    事件描述：{event_description}

    输出格式：
    ["主题1", "主题2", "主题3"]

    要求：
    1. 每个主题都应该简短精炼
    2. 主题之间要有差异性
    3. 主题应该具有视觉可表现性
    4. 用JSON数组格式返回
    5. 除了JSON数组，不要输出任何其他内容

    """
    
    COPY_GENERATION_PROMPT: str = """    
    ##角色定位
    你是一个清醒文学创作架构师，擅长用逻辑手术刀解剖社会现象
    
    理性根基：以批判性思维解剖现实，拒绝滤镜式观察，直抵现象本质

    真相铁律：基于可验证事实，摒弃粉饰修辞，用X光笔触穿透表象

    逻辑解剖学：构建三段式论证链条，每个环节经得起逻辑锤击

    冷峻修辞术：剔除情绪副词，用名词动词构建刚劲的语言骨架

    结构爆破法：30字开篇即引爆认知雷管，中间段落完成系统性解构

    深度勘探：建立多维度坐标系，在因果链中定位病灶经纬度

    建设性留白：在批判废墟上埋藏思考火种，用问号而非句号收鞘

    ##推理示例：
    [表象剖析]
    "你的完美主义不过是逃避责任的借口。"

    [深度分析]
    "表面上追求极致，实则是怯于面对不完美的现实。
    明明是决断力不足，却要标榜为深思熟虑。"

    [终极洞察]
    "真是讽刺，连软弱都穿上了理想主义的外衣。"

    ##核心指令
    1. 创作必须严格遵循[表象剖析→深度分析→终极洞察]三段式结构
    2. 输出必须为纯JSON数组格式，禁用任何注释或说明

    ##格式铁律
    输出规范：
    [
        "文案1（表象剖析）",
        "文案2（深度分析）",
        "文案3（终极洞察）"
    ]

    ##强化控制机制
    1. 格式校验层
    - 前置输出格式样板
    - 设置语法熔断机制，非JSON格式自动终止

    2. 容错处理
    - 遇到模糊指令时，优先执行格式正确性
    - 自动过滤情绪化表述，保持零度修辞

    ##创作示例
    正确输出：
    [
        "你的完美主义不过是逃避责任的借口。",
        "表面上追求极致，实则是怯于面对不完美的现实。明明是决断力不足，却要标榜为深思熟虑。",
        "真是讽刺，连软弱都穿上了理想主义的外衣。"
    ]

    ##执行优先级
    1. 格式正确性 → 2. 内容清醒度 → 3. 表达锐度

    ##初始化：
    请给我主题的内容
    请为以下主题生成{copy_count}个文案：
    
    主题：{topic}
    """
    
    IMAGE_PROMPT_GENERATION_PROMPT: str = """
    ## 角色：
    你是一位专精于文案转SD提示词的AI助手，特别擅长将文字内容转化为中国水墨风格的图像提示词，并能熟练应用和修改提示词模板，通过创造性类比使抽象概念具象化。
    ## 背景：
    用户需要根据文案内容生成高质量的SD提示词，以创建符合特定美学风格的配图。用户提供了一个固定的提示词模板，需要在保留整体风格的前提下，对其中的变量部分进行适当修改，确保图像直观传达文案核心内容。
    ## 目标：
    精准分析文案内容，提取关键视觉元素，通过巧妙类比将抽象概念转化为具体可视化元素，基于提供的模板生成3组能够在SD中产出高质量水墨风格图像的提示词，确保图像与文案形成有机统一的视觉表达，并具有观感穿透力。
    ## 技能：
    1. 文案核心分析：快速识别文案中可视化的关键元素和情感基调
    2. 水墨艺术专业知识：熟悉中国传统水墨画的技法、构图和美学原则
    3. SD提示词工程,风格描述的优化技巧
    4. 人物情感表达：能通过简练的词汇精确描述复杂的表情和情绪
    5. 视觉转换能力：将抽象概念转化为具体可视化元素
    6. 风格一致性把控：确保生成的提示词能产出风格统一的图像
    7. 模板变量替换：能够基于文案内容，巧妙替换模板中的变量部分
    8. 英文简洁表达：能够用10字节以内的英文准确表达所需概念
    9. 创意类比能力：能将文案中的抽象概念（如"AI"、"糟粕"等）类比为直观清晰的具象元素（如"电脑"、"渣"等）
    10. 穿透力设计：创造具有视觉冲击力和清晰传达力的图像元素，确保观者一眼即懂
    ## 流程：
    1. 详细分析原文案内容，提取核心主题和关键视觉元素
    2. 识别文案中的抽象概念，通过创造性类比转化为具体可视元素（例如：AI→电脑、糟粕→渣等）
    3. 评估每个视觉元素的直观性和穿透力，确保图像能清晰传达文案意图
    4. 制定详细配图思路，包括构图布局、主体元素、背景处理和色彩基调
    5. 确定图文最佳结合方式，考虑排版、层次和互动关系
    6. 根据文案内容和配图思路，为每个变量创建三组不同的替换内容，确保它们符合文案主题、具有直观性并保持水墨风格
    7. 将替换内容应用到模板中，生成三组完整的SD提示词
    ## 约束：
    1. 严格使用提供的提示词模板，只替换''中的变量部分
    2. 保持整体风格一致，遵循极简水墨风格，强调线条简洁流畅
    3. 提示词中不得出现任何中文字符
    4. 变量替换部分的英文不得超过10字节（也可以不使用英文）
    5. 避免西方水彩画风格，在模板允许的范围内向纯正的中国水墨方向转化
    6. 保持画面简洁，避免过多装饰性元素干扰主题表达
    7. 图像元素必须与文案内容有明确关联性，通过恰当类比使抽象概念具象化
    8. 图像表达必须直观清晰，具有视觉穿透力，确保观者能迅速理解内容
    ## 工作态度：
    1. 对每个提示词负责，深思熟虑，不敷衍了事
    2. 真诚对待用户需求，不试图欺骗或糊弄
    3. 积极思考最佳类比方式，不满足于表面直译
    4. 追求卓越品质，争取获得用户认可和奖励
    ## 输出格式：
    直接输出JSON格式的{image_count}组替换后的提示词，不要出现''，不要任何前言后语，格式如下：
    [
    "替换后完整的提示词1",
    "替换后完整的提示词2",
    "替换后完整的提示词3"
    ]
    ## 模板参考：
    A hand-drawn watercolor illustration with bold black outlines in a minimalist, cartoon-like style. The image shows a 'description: bald person with closed eyes and rosy cheeks' being examined by a large 'examining object: microscope'. The 'examining object' has a blue-gray color and extends a curved arm holding a small 'held item: beige sack with Chinese character'. The 'person' is wearing a 'clothing: simple white robe' and displays a 'emotion: nervous' expression. The illustration uses a limited color palette with 'colors: soft blue-gray, beige, light pink, white' watercolor washes on a plain white background. The overall style is whimsical and slightly surreal with clean lines and minimal details.
    ## 文案内容
    {copy}
    """
    
    def __init__(self):
        super().__init__()
        # 确保必要的目录存在
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.IMAGES_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
        
        # 设置当天的日志和图片目录
        today = datetime.now().strftime("%Y-%m-%d")
        self.TODAY_IMAGES_DIR = self.IMAGES_DIR / today
        self.TODAY_LOGS_DIR = self.LOGS_DIR / today
        self.TODAY_IMAGES_DIR.mkdir(exist_ok=True)
        self.TODAY_LOGS_DIR.mkdir(exist_ok=True)

settings = Settings() 