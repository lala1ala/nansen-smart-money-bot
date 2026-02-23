"""
配置管理模块
从环境变量读取配置信息
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # Nansen API 配置
    NANSEN_API_KEY = os.getenv('NANSEN_API_KEY')
    NANSEN_BASE_URL = 'https://api.nansen.ai'
    
    # Telegram 配置
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # 时区配置
    TIMEZONE = 'Asia/Shanghai'  # 北京时间
    
    # 支持的区块链（ETH, SOL, BASE）
    CHAINS = ['ethereum', 'solana', 'base']
    
    # 链名称映射
    CHAIN_NAMES = {
        'ethereum': 'ETH',
        'solana': 'SOL',
        'base': 'BASE'
    }
    
    # 每个时间段显示的代币数量
    TOP_TOKENS_COUNT = 10
    
    # API 配置
    API_TIMEOUT = 30  # 秒
    API_RETRY_TIMES = 3
    API_RETRY_DELAY = 2  # 秒
    
    @classmethod
    def validate(cls):
        """验证必需的配置是否存在"""
        errors = []
        
        if not cls.NANSEN_API_KEY:
            errors.append("缺少 NANSEN_API_KEY")
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("缺少 TELEGRAM_BOT_TOKEN")
        if not cls.TELEGRAM_CHAT_ID:
            errors.append("缺少 TELEGRAM_CHAT_ID")
        
        if errors:
            raise ValueError(f"配置错误: {', '.join(errors)}")
        
        return True
