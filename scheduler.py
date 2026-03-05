"""
定时任务调度器
使用 APScheduler + 北京时间 cron 触发器
"""
import logging
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from typing import Callable

logger = logging.getLogger(__name__)

BEIJING_TZ = pytz.timezone('Asia/Shanghai')


class ReportScheduler:
    """基于北京时间的报告调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=BEIJING_TZ)
        self.is_running = False
    
    def setup_jobs(
        self,
        job_6h: Callable,
    ):
        """
        注册一个定时任务：
        - 每6小时整点 (0:00 / 6:00 / 12:00 / 18:00 北京时间): 发送 6h Smart Money 净流入
        """
        # 每6小时整点 (0:00 / 6:00 / 12:00 / 18:00 北京时间)
        self.scheduler.add_job(
            job_6h,
            CronTrigger(hour='0,6,12,18', minute=0, timezone=BEIJING_TZ),
            id='job_6h',
            replace_existing=True
        )
        
        logger.info("✅ 定时任务已注册（北京时间）:")
        logger.info("   - 每6小时 0/6/12/18:00 → 6h Smart Money 净流入")
    
    def start(self):
        """启动调度器"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("✅ 调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
    
    def get_next_run_times(self) -> str:
        """获取所有任务的下次执行时间"""
        lines = []
        for job_id, label in [('job_6h', '每6小时')]:
            job = self.scheduler.get_job(job_id)
            if job and job.next_run_time:
                t = job.next_run_time.astimezone(BEIJING_TZ)
                lines.append(f"  • {label}: {t.strftime('%m-%d %H:%M')}")
        return '\n'.join(lines) if lines else "暂无任务"
