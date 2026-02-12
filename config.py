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
    NANSEN_BASE_URL = 'https://api.nansen.ai/v1'
    
    # Telegram 配置
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # 监控配置
    REPORT_INTERVAL_HOURS = int(os.getenv('REPORT_INTERVAL_HOURS', '2'))
    
    # 支持的区块链
    CHAINS = {
        'ethereum': 'ETH',
        'base': 'BASE',
        'solana': 'SOL',
        'bnb': 'BNB'  # 修正：BSC 的正确标识符是 'bnb'
    }
    
    # 监控时间段（小时）- 简化为只显示24小时数据
    TIME_PERIODS = [24]
    
    # API 配置
    API_TIMEOUT = 30  # 秒
    API_RETRY_TIMES = 3
    API_RETRY_DELAY = 2  # 秒
    
    # 每个时间段显示的代币数量
    TOP_TOKENS_COUNT = 5  # Top 5 流入 + Top 5 流出
    
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
