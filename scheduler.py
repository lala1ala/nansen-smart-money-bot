"""
定时任务调度器
使用 APScheduler 实现定时报告发送
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import asyncio
from typing import Callable


class ReportScheduler:
    """报告调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
    
    def add_job(
        self,
        func: Callable,
        interval_hours: int,
        job_id: str = 'monitoring_report'
    ):
        """
        添加定时任务
        
        Args:
            func: 要执行的异步函数
            interval_hours: 执行间隔（小时）
            job_id: 任务ID
        """
        trigger = IntervalTrigger(hours=interval_hours)
        
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            next_run_time=datetime.now()  # 立即执行一次
        )
        
        print(f"✅ 定时任务已添加: 每 {interval_hours} 小时执行一次")
    
    def start(self):
        """启动调度器"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            print("✅ 调度器已启动")
    
    def stop(self):
        """停止调度器"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            print("⏹️ 调度器已停止")
    
    def get_next_run_time(self, job_id: str = 'monitoring_report') -> str:
        """
        获取下次执行时间
        
        Args:
            job_id: 任务ID
            
        Returns:
            下次执行时间的字符串表示
        """
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            return job.next_run_time.strftime('%Y-%m-%d %H:%M:%S')
        return "未知"
