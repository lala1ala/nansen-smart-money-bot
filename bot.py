"""
Telegram Bot 主程序
处理用户命令和自动发送监控报告
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)
from telegram.constants import ParseMode

from config import Config
from nansen_client import NansenClient
from formatters import MessageFormatter
from scheduler import ReportScheduler

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SmartMoneyBot:
    """智能资金监控 Telegram Bot"""
    
    def __init__(self):
        # 验证配置
        Config.validate()
        
        # 初始化组件
        self.nansen_client = NansenClient(Config.NANSEN_API_KEY)
        self.scheduler = ReportScheduler()
        self.app = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理 /start 命令
        """
        welcome_message = (
            "🤖 *智能资金监控机器人*\n\n"
            "欢迎使用！我会定期为您监控以下区块链上的智能资金活动：\n"
            f"• {', '.join(Config.CHAINS.values())}\n\n"
            "📊 *可用命令：*\n"
            "/report - 立即生成监控报告\n"
            "/status - 查看监控状态\n"
            "/help - 显示帮助信息\n\n"
            f"⏰ 自动报告间隔：每 {Config.REPORT_INTERVAL_HOURS} 小时"
        )
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理 /help 命令
        """
        help_text = (
            "📖 *使用帮助*\n\n"
            "*监控内容：*\n"
            "• 监控 ETH、BASE、SOL、BSC 四条链\n"
            "• 追踪智能资金和机构的交易活动\n"
            "• 统计 2h、4h、12h、24h 时间段数据\n\n"
            "*报告内容：*\n"
            "• 买入最多的代币（按交易额排序）\n"
            "• 卖出最多的代币（按交易额排序）\n"
            "• 每个时间段显示前 5 个代币\n\n"
            "*命令说明：*\n"
            "/start - 启动机器人\n"
            "/report - 立即生成报告\n"
            "/status - 查看监控状态\n"
            "/help - 显示本帮助信息\n\n"
            "💡 数据来源：Nansen"
        )
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理 /status 命令
        """
        status_message = MessageFormatter.format_status_message()
        next_run = self.scheduler.get_next_run_time()
        
        status_message += f"\n\n⏰ 下次报告时间：{next_run}"
        
        await update.message.reply_text(
            status_message,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理 /report 命令 - 立即生成报告
        """
        # 发送"正在生成"消息
        status_msg = await update.message.reply_text("🔄 正在生成报告，请稍候...")
        
        try:
            # 生成报告
            await self.send_report(context)
            
            # 删除状态消息
            await status_msg.delete()
            
        except Exception as e:
            logger.error(f"生成报告失败: {str(e)}")
            await status_msg.edit_text(
                MessageFormatter.format_error_message(str(e)),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def send_report(self, context: ContextTypes.DEFAULT_TYPE):
        """
        生成并发送监控报告到指定频道
        
        Args:
            context: Telegram 上下文
        """
        try:
            logger.info("开始生成监控报告...")
            
            # 获取监控数据
            report_data = self.nansen_client.get_monitoring_report()
            
            # 格式化消息
            message = MessageFormatter.format_report(report_data)
            
            # 发送到指定频道/聊天
            await context.bot.send_message(
                chat_id=Config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info("✅ 报告发送成功")
            
        except Exception as e:
            logger.error(f"发送报告失败: {str(e)}")
            
            # 发送错误消息
            error_msg = MessageFormatter.format_error_message(str(e))
            await context.bot.send_message(
                chat_id=Config.TELEGRAM_CHAT_ID,
                text=error_msg,
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def scheduled_report(self):
        """
        定时任务：发送报告
        """
        # 创建一个临时的 context 对象用于发送消息
        await self.send_report(self.app.bot)
    
    def run(self):
        """
        启动 bot
        """
        # 创建应用
        self.app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # 注册命令处理器
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("report", self.report_command))
        
        # 设置定时任务
        async def send_scheduled_report(context: ContextTypes.DEFAULT_TYPE):
            await self.send_report(context)
        
        self.scheduler.add_job(
            lambda: asyncio.create_task(send_scheduled_report(self.app.bot)),
            Config.REPORT_INTERVAL_HOURS
        )
        self.scheduler.start()
        
        # 启动 bot
        logger.info("🤖 Bot 启动中...")
        logger.info(f"📡 监控链: {', '.join(Config.CHAINS.values())}")
        logger.info(f"⏰ 报告间隔: 每 {Config.REPORT_INTERVAL_HOURS} 小时")
        
        # 运行
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """主函数"""
    try:
        bot = SmartMoneyBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("👋 Bot 已停止")
    except Exception as e:
        logger.error(f"❌ Bot 运行错误: {str(e)}")
        raise


if __name__ == '__main__':
    main()
