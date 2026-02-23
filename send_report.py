"""
GitHub Actions 专用脚本
每30分钟被 GitHub Actions 调用一次。
根据当前北京时间决定发送哪些时间段的图片：
  - 每30分钟 (:30) → 10min
  - 每整点   (:00) → 10min + 1h
  - 6小时整点 (0/6/12/18:00 BJT) → 10min + 1h + 6h
"""
import asyncio
import sys
from datetime import datetime
import pytz

from config import Config
from nansen_client import NansenClient
from image_renderer import render_netflow_image
from telegram import Bot


BEIJING_TZ = pytz.timezone('Asia/Shanghai')


def get_timeframes_for_now() -> list[str]:
    """根据当前北京时间决定要发送的时间段"""
    now = datetime.now(BEIJING_TZ)
    minute = now.minute
    hour   = now.hour

    if minute == 0:
        if hour % 6 == 0:
            print(f"🕐 北京时间 {hour:02d}:00 → 发送 10min + 1h + 6h")
            return ['10m', '1h', '6h']
        else:
            print(f"🕐 北京时间 {hour:02d}:00 → 发送 10min + 1h")
            return ['10m', '1h']
    else:
        print(f"🕐 北京时间 {hour:02d}:{minute:02d} → 发送 10min")
        return ['10m']


async def send_report_once():
    """根据当前时间发送对应的图片报告"""
    try:
        Config.validate()
        print("✅ 配置验证通过")

        timeframes = get_timeframes_for_now()

        nansen_client = NansenClient(Config.NANSEN_API_KEY)
        bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)

        data = nansen_client.get_screener_for_report(timeframes)

        for tf in timeframes:
            tokens = data.get(tf, [])
            print(f"📊 {tf}: 获取到 {len(tokens)} 个代币")

            image_buf = render_netflow_image(tokens, tf)
            tf_label = {'10m': '10分钟', '1h': '1小时', '6h': '6小时'}.get(tf, tf)

            await bot.send_photo(
                chat_id=Config.TELEGRAM_CHAT_ID,
                photo=image_buf,
                caption=f"📊 Smart Money 净流入 Top{len(tokens)} | {tf_label}",
            )
            print(f"✅ {tf} 图片发送成功")

        return 0

    except Exception as e:
        print(f"❌ 错误: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(send_report_once())
    sys.exit(exit_code)
