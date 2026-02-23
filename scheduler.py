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
        job_30min: Callable,
        job_1h: Callable,
        job_6h: Callable,
    ):
        """
        注册三个定时任务：
        - 每30分钟（非整点）: 发送 10min 报告
        - 每整点:            发送 10min + 1h 报告
        - 每6小时整点:       发送 10min + 1h + 6h 报告
        
        调度逻辑（北京时间）:
        - 6h 任务在 0/6/12/18 整点触发
        - 1h 任务在每小时 :00 触发（但 6h 整点由 6h 任务负责，cron 会重叠，先注册的优先）
        - 30min 任务在每小时 :30 触发
        """
        # 每6小时整点 (0:00 / 6:00 / 12:00 / 18:00 北京时间)
        self.scheduler.add_job(
            job_6h,
            CronTrigger(hour='0,6,12,18', minute=0, timezone=BEIJING_TZ),
            id='job_6h',
            replace_existing=True
        )
        
        # 每整点（非6h整点剔除其实不需要，APScheduler 会同时触发多个，我们在 bot 侧判断）
        # 为了简化，1h 任务每整点都触发，bot 侧检测若是6h时间则跳过（6h 任务已处理）
        self.scheduler.add_job(
            job_1h,
            CronTrigger(minute=0, timezone=BEIJING_TZ),
            id='job_1h',
            replace_existing=True
        )
        
        # 每30分钟（:30 分）
        self.scheduler.add_job(
            job_30min,
            CronTrigger(minute=30, timezone=BEIJING_TZ),
            id='job_30min',
            replace_existing=True
        )
        
        logger.info("✅ 定时任务已注册（北京时间）:")
        logger.info("   - 每30分钟 :30 → 10min 净流入")
        logger.info("   - 每小时   :00 → 10min + 1h 净流入")
        logger.info("   - 每6小时  0/6/12/18:00 → 10min + 1h + 6h 净流入")
    
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
        for job_id, label in [('job_30min', '每30分钟'), ('job_1h', '每小时'), ('job_6h', '每6小时')]:
            job = self.scheduler.get_job(job_id)
            if job and job.next_run_time:
                t = job.next_run_time.astimezone(BEIJING_TZ)
                lines.append(f"  • {label}: {t.strftime('%m-%d %H:%M')}")
        return '\n'.join(lines) if lines else "暂无任务"
