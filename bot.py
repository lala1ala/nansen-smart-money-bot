"""
Telegram Bot 主程序
Smart Money 净流入图片报告 - 北京时间定时发送
"""
import asyncio
import logging
import pytz
from datetime import datetime
from io import BytesIO

from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

from config import Config
from nansen_client import NansenClient
from image_renderer import render_netflow_image
from scheduler import ReportScheduler, BEIJING_TZ

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SmartMoneyBot:
    """Smart Money 净流入图片报告 Bot"""

    def __init__(self):
        Config.validate()
        self.nansen_client = NansenClient(Config.NANSEN_API_KEY)
        self.scheduler = ReportScheduler()
        self.app = None

    # ─────────────────────────────────────────────────────
    #  核心发送逻辑
    # ─────────────────────────────────────────────────────

    async def _send_images(self, bot: Bot, timeframes: list[str]):
        """
        获取数据 → 渲染图片 → 发送到 Telegram
        
        Args:
            bot: Telegram Bot 实例
            timeframes: 要发送的时间段列表，顺序即发送顺序
        """
        data = self.nansen_client.get_screener_for_report(timeframes)

        for tf in timeframes:
            tokens = data.get(tf, [])
            try:
                image_buf: BytesIO = render_netflow_image(tokens, tf)
                tf_label = {'10m': '10分钟', '1h': '1小时', '6h': '6小时'}.get(tf, tf)
                await bot.send_photo(
                    chat_id=Config.TELEGRAM_CHAT_ID,
                    photo=image_buf,
                    caption=f"📊 Smart Money 净流入 Top{len(tokens)} | {tf_label}",
                )
                logger.info(f"✅ 已发送 {tf} 图片 ({len(tokens)} 个代币)")
            except Exception as e:
                logger.error(f"❌ 发送 {tf} 图片失败: {e}")
                await bot.send_message(
                    chat_id=Config.TELEGRAM_CHAT_ID,
                    text=f"⚠️ {tf} 报告生成失败: {str(e)}"
                )

    # ─────────────────────────────────────────────────────
    #  定时任务回调
    # ─────────────────────────────────────────────────────

    async def _job_6h(self):
        """每6小时整点 (0/6/12/18:00 北京时间) → 发送 6h Smart Money 净流入"""
        now = datetime.now(BEIJING_TZ)
        logger.info(f"⏰ 触发 6h 任务 ({now.hour}:00) → 发送 6h 图片")
        await self._send_images(self.app.bot, ['6h'])

    # ─────────────────────────────────────────────────────
    #  Telegram 命令
    # ─────────────────────────────────────────────────────

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chains_str = " · ".join(
            Config.CHAIN_NAMES[c] for c in Config.CHAINS
        )
        welcome = (
            "🤖 *Smart Money 净流入监控*\n\n"
            f"📡 监控链: {chains_str}\n"
            f"📊 显示: Top{Config.TOP_TOKENS_COUNT} 净流入代币\n\n"
            "⏰ *发送计划（北京时间）*\n"
            "  • 每6小时 (0/6/12/18:00) → 6h Smart Money 净流入\n\n"
            "📌 *命令*\n"
            "/report - 立即发送 6h 报告\n"
            "/status - 查看下次任务时间\n"
            "/help - 帮助"
        )
        await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = (
            "📖 *使用帮助*\n\n"
            "*监控内容：*\n"
            "  Nansen Token Screener Smart Money 净流入 (6小时)\n"
            "  链：ETH · SOL · BASE\n\n"
            "*图片内容：*\n"
            f"  排名 / Token / 价格 / 链 / 交易者数 / 净流入金额\n\n"
            "*命令：*\n"
            "  /report - 立即生成并发送 6h 报告\n"
            "  /status - 查看下次定时任务时间\n"
            "  /start  - 重新显示介绍\n\n"
            "💡 数据源: Nansen Smart Money"
        )
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        next_times = self.scheduler.get_next_run_times()
        now = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M')
        status = (
            f"✅ *监控运行中*\n\n"
            f"🕰 当前北京时间: {now}\n\n"
            f"⏰ *下次任务时间：*\n{next_times}"
        )
        await update.message.reply_text(status, parse_mode=ParseMode.MARKDOWN)

    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """手动触发 6h 报告"""
        msg = await update.message.reply_text("🔄 正在生成 6h 报告，请稍候...")
        try:
            await self._send_images(context.bot, ['6h'])
            await msg.delete()
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            await msg.edit_text(f"⚠️ 报告生成失败: {str(e)}")

    # ─────────────────────────────────────────────────────
    #  启动
    # ─────────────────────────────────────────────────────

    def run(self):
        """启动 bot"""
        self.app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

        # 注册命令
        self.app.add_handler(CommandHandler("start",  self.start_command))
        self.app.add_handler(CommandHandler("help",   self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("report", self.report_command))

        # APScheduler 需要在 event loop 内注册异步任务
        async def post_init(app: Application):
            self.scheduler.setup_jobs(
                job_6h=self._job_6h,
            )
            self.scheduler.start()

        self.app.post_init = post_init

        logger.info("🤖 Smart Money Bot 启动中...")
        logger.info(f"📡 监控链: ETH · SOL · BASE")
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
