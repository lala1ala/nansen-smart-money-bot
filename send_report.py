"""
GitHub Actions 专用脚本
仅发送一次报告，然后退出
"""
import asyncio
import sys
from config import Config
from nansen_client import NansenClient
from formatters import MessageFormatter
from telegram import Bot
from telegram.constants import ParseMode


async def send_report_once():
    """发送一次监控报告"""
    try:
        # 验证配置
        Config.validate()
        print("✅ 配置验证通过")
        
        # 初始化 Nansen 客户端
        print("📡 正在获取监控数据...")
        nansen_client = NansenClient(Config.NANSEN_API_KEY)
        report_data = nansen_client.get_monitoring_report()
        
        # 格式化消息
        print("📝 正在格式化报告...")
        message = MessageFormatter.format_report(report_data)
        
        # 发送到 Telegram
        print(f"📤 正在发送报告到 Chat ID: {Config.TELEGRAM_CHAT_ID}")
        bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=Config.TELEGRAM_CHAT_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        print("✅ 报告发送成功！")
        return 0
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(send_report_once())
    sys.exit(exit_code)
