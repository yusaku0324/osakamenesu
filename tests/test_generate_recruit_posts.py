#!/usr/bin/env python3
"""
generate_recruit_posts.pyのテスト
"""
import json
import sys
from unittest.mock import MagicMock, call, patch

import pytest

import generate_recruit_posts


@pytest.fixture
def mock_openai_response():
    """OpenAI APIのモックレスポンス"""

    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockChoice:
        def __init__(self, message):
            self.message = message

    class MockResponse:
        def __init__(self, choices):
            self.choices = choices

    message = MockMessage(
        "✨ 【急募】都内高級メンズエステ♪日給3万円以上💰 未経験大歓迎！研修充実で安心♪ 日払いOK！ 応募はDMまで！ #メンエス求人 #高収入 #日払い"
    )
    choice = MockChoice(message)
    return MockResponse([choice])


@pytest.fixture
def mock_tweepy_response():
    """Tweepy APIのモックレスポンス"""

    class MockData:
        def __init__(self):
            self.data = {"id": "1234567890"}

    return MockData()


def test_generate_recruit_post(mock_openai_response):
    """generate_recruit_post関数のテスト"""
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_openai_response
        mock_openai.return_value = mock_client

        result = generate_recruit_posts.generate_recruit_post()

        assert isinstance(result, str)
        assert len(result) > 0
        assert mock_client.chat.completions.create.called


def test_post_to_twitter(mock_tweepy_response):
    """post_to_twitter関数のテスト"""
    with patch("tweepy.Client") as mock_tweepy:
        mock_client = MagicMock()
        mock_client.create_tweet.return_value = mock_tweepy_response
        mock_tweepy.return_value = mock_client

        result = generate_recruit_posts.post_to_twitter("テストツイート")

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "tweet_id" in result
        assert mock_client.create_tweet.called


def test_post_to_twitter_error():
    """post_to_twitter関数のエラーケーステスト"""
    with patch("tweepy.Client") as mock_tweepy:
        mock_client = MagicMock()
        mock_client.create_tweet.side_effect = Exception("テストエラー")
        mock_tweepy.return_value = mock_client

        result = generate_recruit_posts.post_to_twitter("テストツイート")

        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result


def test_add_emojis():
    """add_emojis関数のテスト"""
    text = "テストテキスト"
    result = generate_recruit_posts.add_emojis(text)

    assert isinstance(result, str)
    assert text in result
    assert len(result) > len(text)


@patch("generate_recruit_posts.generate_recruit_post")
@patch("generate_recruit_posts.post_to_twitter")
def test_main_success(mock_post, mock_generate):
    """main関数の成功ケーステスト"""
    mock_generate.return_value = "テストツイート"
    mock_post.return_value = {"success": True, "tweet_id": "1234567890"}

    result = generate_recruit_posts.main()

    assert result == 0
    assert mock_generate.called
    assert mock_post.called


@patch("generate_recruit_posts.generate_recruit_post")
@patch("generate_recruit_posts.post_to_twitter")
def test_main_failure(mock_post, mock_generate):
    """main関数の失敗ケーステスト"""
    mock_generate.return_value = "テストツイート"
    mock_post.return_value = {"success": False, "error": "テストエラー"}

    result = generate_recruit_posts.main()

    assert result == 1
    assert mock_generate.called
    assert mock_post.called


@patch("generate_recruit_posts.generate_recruit_post")
def test_main_unicode_error(mock_generate):
    """main関数のUnicodeEncodeErrorケーステスト"""

    # 例外を直接モックする代わりに、例外を発生させる関数をパッチする
    def side_effect():
        # 最初の呼び出しでUnicodeEncodeErrorを発生させる
        if mock_generate.call_count == 1:
            # UnicodeEncodeErrorを発生させる
            class FakeUnicodeError(UnicodeEncodeError):
                def __init__(self):
                    pass

            raise FakeUnicodeError()
        # 2回目の呼び出しで正常に戻る
        return "テストツイート"

    mock_generate.side_effect = side_effect

    with patch("generate_recruit_posts.post_to_twitter") as mock_post:
        mock_post.return_value = {"success": True, "tweet_id": "1234567890"}

        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = "ascii"

            with patch("sys.stdout.reconfigure") as mock_reconfigure:
                result = generate_recruit_posts.main()

                assert result == 0
                assert mock_generate.call_count == 2
                assert mock_post.called


@patch("generate_recruit_posts.generate_recruit_post")
def test_main_unexpected_error(mock_generate):
    """main関数の予期しないエラーケーステスト"""
    mock_generate.side_effect = Exception("予期しないエラー")

    result = generate_recruit_posts.main()

    assert result == 1
    assert mock_generate.called
