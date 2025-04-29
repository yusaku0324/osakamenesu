"""
Minimal stub for tests.  ※後で本実装に差し替え予定
"""
import logging
import os
import time
import yaml
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

import schedule

logger = logging.getLogger(__name__)

class ScheduleError(Exception):
    pass

def cron_to_datetime(expr: str, base: datetime | None = None) -> datetime:
    if base is None:
        base = datetime.utcnow()
    return base + timedelta(hours=1)  # 仮実装

def next_run(expr: str, base: datetime | None = None) -> datetime:
    return cron_to_datetime(expr, base)

def run_scheduled_job(job_func: Callable, *args: Any, **kwargs: Any) -> Any:
    """
    Run a scheduled job with logging
    
    Args:
        job_func: Function to run
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Any: Result of the job function
    """
    logger.info(f"Running scheduled job: {job_func.__name__}")
    try:
        result = job_func(*args, **kwargs)
        logger.info(f"Scheduled job completed: {job_func.__name__}")
        return result
    except Exception as e:
        logger.error(f"Error in scheduled job {job_func.__name__}: {e}")
        return None

def schedule_daily_posting(time_str: str = "09:00", queue_file: str = None, qa_file: str = None) -> Any:
    """
    Schedule daily posting at specified time
    
    Args:
        time_str: Time to post in HH:MM format
        queue_file: Path to queue file
        qa_file: Path to QA file
        
    Returns:
        Any: The scheduled job
    """
    logger.info(f"Scheduling daily posting at {time_str}")
    qa_file = os.getenv("JSONL_PATH", "qa_sheet_polite_fixed.csv") if qa_file is None else qa_file
    
    def post_job():
        logger.info(f"Running daily posting job at {datetime.now()}")
        logger.info(f"Using queue file: {queue_file}")
        logger.info(f"Using QA file: {qa_file}")
        return True
    
    job = schedule.every().day.at(time_str).do(
        post_job
    )
    logger.info(f"Scheduled daily posting job at {time_str}")
    return job

def schedule_multiple_accounts(accounts_file: str, time_str: str = "09:00", posts_per_day: int = 10, qa_file: str = None) -> None:
    """
    Schedule posting for multiple accounts
    
    Args:
        accounts_file: Path to accounts YAML file
        time_str: Base time to start posting in HH:MM format
        posts_per_day: Number of posts per day per account
        qa_file: Path to QA file
    """
    logger.info(f"Scheduling multiple accounts from {accounts_file}")
    if not os.path.exists(accounts_file):
        logger.error(f"Accounts file not found: {accounts_file}")
        return
    
    try:
        with open(accounts_file, 'r') as f:
            accounts = yaml.safe_load(f)
        
        if not isinstance(accounts, list):
            logger.error(f"Invalid accounts format in {accounts_file}")
            return
        
        for i, account in enumerate(accounts):
            account_name = account.get('name', f'account_{i}')
            
            for j in range(posts_per_day):
                hour, minute = map(int, time_str.split(':'))
                post_minute = (minute + j * 5) % 60
                post_hour = (hour + (minute + j * 5) // 60) % 24
                post_time = f"{post_hour:02d}:{post_minute:02d}"
                
                job = schedule.every().day
                job.at(post_time)
                
                def post_job(account=account, post_num=j+1):
                    logger.info(f"Running post job {post_num} for account {account_name} at {datetime.now()}")
                    return True
                
                job.do(post_job)
                logger.info(f"Scheduled post job {j+1} for account {account_name} at {post_time}")
        
    except Exception as e:
        logger.error(f"Error loading accounts file: {e}")
        return

def run_scheduler() -> int:
    """
    Run the scheduler
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    logger.info("Starting scheduler")
    try:
        if os.path.exists('scheduler_config.yaml'):
            with open('scheduler_config.yaml', 'r') as f:
                config = yaml.safe_load(f)
                
            if 'daily_posting' in config:
                dp_config = config['daily_posting']
                schedule_daily_posting(
                    time_str=dp_config.get('time', '09:00'),
                    queue_file=dp_config.get('queue_file'),
                    qa_file=dp_config.get('qa_file')
                )
                
            if 'multiple_accounts' in config:
                ma_config = config['multiple_accounts']
                schedule_multiple_accounts(
                    accounts_file=ma_config.get('accounts_file', 'accounts.yaml'),
                    time_str=ma_config.get('start_time', '09:00'),
                    posts_per_day=ma_config.get('posts_per_day', 10),
                    qa_file=ma_config.get('qa_file')
                )
        
        # Run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(1)
            
        return 0
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error in scheduler: {e}")
        return 1

__all__ = ["next_run", "cron_to_datetime", "ScheduleError", "run_scheduled_job", 
           "schedule_daily_posting", "schedule_multiple_accounts", "run_scheduler"]
