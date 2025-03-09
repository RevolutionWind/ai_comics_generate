from loguru import logger
from datetime import datetime
from pathlib import Path
from ..config import settings

def setup_logger():
    # 获取今天的日期
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = settings.TODAY_LOGS_DIR / f"process_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 配置logger
    logger.add(
        log_file,
        rotation="500 MB",
        encoding="utf-8",
        enqueue=True,
        compression="zip",
        retention="10 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    
    return logger

# 创建logger实例
log = setup_logger() 