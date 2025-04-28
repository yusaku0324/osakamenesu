"""
Scheduling module for automated Q&A video generation and X posting
"""
import os
import sys
import time
import logging
import schedule
import datetime
import random
import yaml
from typing import Callable, Dict, Any, Optional, List, Union

from bot.utils.log import setup_logger
from bot.main import process_queue

logger = setup_logger("scheduler", "scheduler.log")

def run_scheduled_job(job_func: Callable, *args, **kwargs) -> None:
    """
    スケジュールされたジョブを実行する
    
    Args:
        job_func: 実行する関数
        *args: 位置引数
        **kwargs: キーワード引数
    """
    try:
        logger.info(f"Running scheduled job: {job_func.__name__}")
        job_func(*args, **kwargs)
        logger.info(f"Scheduled job completed: {job_func.__name__}")
    except Exception as e:
        logger.error(f"Error in scheduled job {job_func.__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())

def schedule_daily_posting(time_str: str = "09:00", queue_file: Optional[str] = None, 
                          qa_file: Optional[str] = None) -> None:
    """
    毎日の投稿をスケジュールする
    
    Args:
        time_str: 実行時刻（HH:MM形式）
        queue_file: キューファイルのパス（Noneの場合は自動生成）
        qa_file: Q&Aデータファイルのパス（Noneの場合はデフォルト）
    """
    try:
        logger.info(f"Scheduling daily posting at {time_str}")
        
        if not qa_file:
            qa_file = os.getenv("JSONL_PATH", "qa_sheet_polite_fixed.csv")
            logger.info(f"Using default Q&A file: {qa_file}")
        
        schedule.every().day.at(time_str).do(
            run_scheduled_job, 
            process_queue, 
            queue_file=queue_file, 
            qa_file=qa_file
        )
        
        logger.info(f"Daily posting scheduled at {time_str}")
    except Exception as e:
        logger.error(f"Error scheduling daily posting: {e}")
        import traceback
        logger.error(traceback.format_exc())

def schedule_multiple_accounts(accounts_file: str, time_str: str = "09:00", 
                              posts_per_day: int = 10, qa_file: Optional[str] = None) -> None:
    """
    複数アカウントの投稿をスケジュールする
    
    Args:
        accounts_file: アカウント設定ファイルのパス
        time_str: 開始時刻（HH:MM形式）
        posts_per_day: 1日あたりの投稿数
        qa_file: Q&Aデータファイルのパス（Noneの場合はデフォルト）
    """
    try:
        logger.info(f"Scheduling multiple accounts posting from {accounts_file}")
        
        if not os.path.exists(accounts_file):
            logger.error(f"Accounts file not found: {accounts_file}")
            return
        
        import yaml
        with open(accounts_file, 'r', encoding='utf-8') as f:
            accounts = yaml.safe_load(f)
        
        if not isinstance(accounts, list):
            logger.error(f"Invalid accounts format in {accounts_file}")
            return
        
        logger.info(f"Loaded {len(accounts)} accounts from {accounts_file}")
        
        if not qa_file:
            qa_file = os.getenv("JSONL_PATH", "qa_sheet_polite_fixed.csv")
            logger.info(f"Using default Q&A file: {qa_file}")
        
        total_posts = len(accounts) * posts_per_day
        interval_minutes = int(24 * 60 / total_posts)
        
        logger.info(f"Scheduling {total_posts} posts with {interval_minutes} minutes interval")
        
        hour, minute = map(int, time_str.split(':'))
        start_time = datetime.time(hour=hour, minute=minute)
        
        for i, account in enumerate(accounts):
            account_name = account.get('name', f"account_{i+1}")
            cookie_path = account.get('cookie_path', '')
            
            if not cookie_path or not os.path.exists(cookie_path):
                logger.warning(f"Invalid cookie path for account {account_name}: {cookie_path}")
                continue
            
            for j in range(posts_per_day):
                post_index = i * posts_per_day + j
                minutes_offset = post_index * interval_minutes
                
                post_time = datetime.datetime.combine(
                    datetime.date.today(), start_time
                ) + datetime.timedelta(minutes=minutes_offset)
                
                post_time_str = post_time.strftime("%H:%M")
                
                env_vars = {
                    "ACCOUNT_NAME": account_name,
                    "COOKIE_PATH": cookie_path,
                    "POST_INDEX": str(j+1)
                }
                
                schedule.every().day.at(post_time_str).do(
                    run_scheduled_job,
                    process_queue,
                    queue_file=None,  # 自動生成
                    qa_file=qa_file,
                    env_vars=env_vars
                )
                
                logger.info(f"Scheduled post {j+1} for account {account_name} at {post_time_str}")
        
        logger.info(f"Multiple accounts posting scheduled successfully")
    except Exception as e:
        logger.error(f"Error scheduling multiple accounts: {e}")
        import traceback
        logger.error(traceback.format_exc())

def run_scheduler() -> int:
    """
    スケジューラを実行する
    
    Returns:
        int: 終了コード（0: 成功、1: 失敗）
    """
    try:
        logger.info("Starting scheduler")
        
        config_file = os.getenv("SCHEDULER_CONFIG", "scheduler_config.yaml")
        
        if os.path.exists(config_file):
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'daily_posting' in config:
                daily_config = config['daily_posting']
                schedule_daily_posting(
                    time_str=daily_config.get('time', '09:00'),
                    queue_file=daily_config.get('queue_file'),
                    qa_file=daily_config.get('qa_file')
                )
            
            if 'multiple_accounts' in config:
                multi_config = config['multiple_accounts']
                schedule_multiple_accounts(
                    accounts_file=multi_config.get('accounts_file', 'accounts.yaml'),
                    time_str=multi_config.get('start_time', '09:00'),
                    posts_per_day=multi_config.get('posts_per_day', 10),
                    qa_file=multi_config.get('qa_file')
                )
        else:
            logger.info(f"Config file not found: {config_file}, using default schedule")
            schedule_daily_posting()
        
        logger.info("Running scheduler loop")
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Error in scheduler: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(run_scheduler())
