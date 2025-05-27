# models.py - データモデル定義
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Tweet:
    """ツイート情報を表すデータクラス"""
    id: str
    username: str
    text: str
    timestamp: datetime
    url: str


@dataclass
class Campaign:
    """DMキャンペーンを表すデータクラス"""
    name: str
    keywords: List[str]
    message_templates: List[str]
    max_dms_per_hour: int
    check_interval: int
    recipient_list: Optional[List[str]] = None
    exclude_list: Optional[List[str]] = None
    active: bool = True