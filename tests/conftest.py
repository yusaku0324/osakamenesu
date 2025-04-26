"""
テスト用の共通フィクスチャ
"""
import pytest
import os
import sys
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_env_vars():
    """環境変数のモック"""
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_openai_key",
        "TWITTER_BEARER_TOKEN": "test_twitter_token"
    }):
        yield
