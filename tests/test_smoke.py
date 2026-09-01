"""Smoke tests for HiveMind-matrix-bridge.

These tests import the package, check the version, and construct the bridge
with a mocked Matrix client and a mocked HiveMind solver so no live network
connections are made.
"""
from unittest.mock import MagicMock, patch

import hm_matrix_bridge
from hm_matrix_bridge.version import __version__


def test_version_is_a_string():
    assert isinstance(__version__, str)
    assert __version__
    # version.py VERSION_BLOCK -> dotted version
    assert __version__.split("a")[0].count(".") == 2


def test_package_exports_bridge():
    assert hasattr(hm_matrix_bridge, "HiveMindMatrixBridge")


def _make_bridge(bot_mention="thehivebot"):
    """Build a bridge with MatrixBot and HiveMindSolver mocked out."""
    with patch("hm_matrix_bridge.MatrixBot") as mock_bot_cls, \
            patch("hm_matrix_bridge.HiveMindSolver") as mock_solver_cls:
        mock_bot = MagicMock()
        mock_bot.bot_mention = bot_mention
        mock_bot_cls.return_value = mock_bot

        mock_solver = MagicMock()
        mock_solver_cls.return_value = mock_solver

        bridge = hm_matrix_bridge.HiveMindMatrixBridge(
            matrix_host="https://matrix.example",
            matrix_token="fake-token",
            room_alias="#test:matrix.example",
            bot_mention=bot_mention,
        )
        return bridge, mock_bot, mock_solver


def test_bridge_construction_no_live_connections():
    bridge, mock_bot, mock_solver = _make_bridge()
    assert bridge.platform.startswith("HiveMindMatrixBridge")
    # the bridge wires its handler onto the bot
    assert mock_bot.on_message == bridge.handle_matrix_utterance


def test_handle_utterance_when_mentioned():
    bridge, mock_bot, mock_solver = _make_bridge()
    mock_solver.get_spoken_answer.return_value = "hello back"

    event = {
        "sender": "@user:matrix.example",
        "content": {"body": "thehivebot what time is it"},
    }
    bridge.handle_matrix_utterance(event)

    mock_solver.get_spoken_answer.assert_called_once()
    asked = mock_solver.get_spoken_answer.call_args[0][0]
    assert "thehivebot" not in asked
    mock_bot.room.send_text.assert_called_once_with("hello back")


def test_handle_utterance_ignored_when_not_mentioned():
    bridge, mock_bot, mock_solver = _make_bridge()

    event = {
        "sender": "@user:matrix.example",
        "content": {"body": "just chatting, no mention"},
    }
    bridge.handle_matrix_utterance(event)

    mock_solver.get_spoken_answer.assert_not_called()
    mock_bot.room.send_text.assert_not_called()


def test_handle_utterance_respond_to_all_when_no_mention_configured():
    """With no --botname configured, bot_mention is None and every
    utterance that reaches the handler should be answered, not crash."""
    bridge, mock_bot, mock_solver = _make_bridge(bot_mention=None)
    mock_solver.get_spoken_answer.return_value = "hello back"

    event = {
        "sender": "@user:matrix.example",
        "content": {"body": "what time is it"},
    }
    bridge.handle_matrix_utterance(event)

    mock_solver.get_spoken_answer.assert_called_once_with("what time is it")
    mock_bot.room.send_text.assert_called_once_with("hello back")
