"""Unit tests for interactive TelegramBotService."""

from unittest.mock import patch, MagicMock
from level_crossing.alerts.bot_service import TelegramBotService


def test_telegram_bot_service_init():
    service = TelegramBotService(bot_token="test_token_123")
    assert service.is_configured is True
    assert service.is_running is False


def test_telegram_bot_service_unconfigured():
    service = TelegramBotService(bot_token="")
    assert service.is_configured is False
    assert service.start() is False


@patch("requests.post")
def test_telegram_bot_service_handle_start(mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    service = TelegramBotService(bot_token="dummy_token")

    message = {
        "message_id": 1,
        "from": {"id": 1295515495, "first_name": "Aditya", "username": "Adi_1_12"},
        "chat": {"id": 1295515495, "type": "private"},
        "text": "/start",
    }

    service._handle_message(message)
    assert mock_post.called
    args, kwargs = mock_post.call_args
    assert "https://api.telegram.org/botdummy_token/sendMessage" in args[0]
    payload = kwargs["json"]
    assert payload["chat_id"] == 1295515495
    assert "1295515495" in payload["text"]
    assert "Welcome Aditya" in payload["text"]


@patch("requests.post")
def test_telegram_bot_service_handle_status(mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    service = TelegramBotService(bot_token="dummy_token")

    message = {
        "message_id": 2,
        "from": {"id": 1295515495, "first_name": "Aditya"},
        "chat": {"id": 1295515495},
        "text": "/status",
    }

    service._handle_message(message)
    assert mock_post.called
    payload = mock_post.call_args[1]["json"]
    assert "RAILWAY SAFETY SYSTEM HEALTH" in payload["text"]
    assert "YOLOv8" in payload["text"]


@patch("requests.post")
def test_telegram_bot_service_handle_ping(mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    service = TelegramBotService(bot_token="dummy_token")

    message = {
        "message_id": 3,
        "from": {"id": 1295515495},
        "chat": {"id": 1295515495},
        "text": "/ping",
    }

    service._handle_message(message)
    assert mock_post.called
    payload = mock_post.call_args[1]["json"]
    assert "Pong" in payload["text"]
