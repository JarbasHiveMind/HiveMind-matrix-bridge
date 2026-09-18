"""Sends are paced, and a send the server holds is reported.

A homeserver rate limits a client that talks faster than its budget.
``matrix_client`` answers a 429 by sleeping the ``retry_after_ms`` the server
names and trying again — on the calling thread, with no bound on the retries
and no log line. In this bridge the caller is the listener thread, so a
rate-limited bridge stops receiving while it waits, and looks like a bridge
that has died. Pacing keeps it out of that state; the warning makes it visible
when it gets there anyway.
"""
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from hm_matrix_bridge import matrixapi
from hm_matrix_bridge.matrixapi import MatrixBot


def _bot(min_send_interval=None):
    """A MatrixBot with the network constructor bypassed."""
    bot = MatrixBot.__new__(MatrixBot)
    bot.room = MagicMock()
    bot.min_send_interval = (matrixapi.DEFAULT_MIN_SEND_INTERVAL
                             if min_send_interval is None
                             else float(min_send_interval))
    bot._send_lock = threading.Lock()
    bot._last_send = 0.0
    return bot


class TestPacing(unittest.TestCase):

    def test_the_first_send_is_not_delayed(self):
        bot = _bot(min_send_interval=5.0)
        started = time.monotonic()
        bot.send_text("hello")
        self.assertLess(time.monotonic() - started, 1.0)
        bot.room.send_text.assert_called_once_with("hello")

    def test_a_second_send_waits_the_interval(self):
        bot = _bot(min_send_interval=0.2)
        bot.send_text("one")
        started = time.monotonic()
        bot.send_text("two")
        self.assertGreaterEqual(time.monotonic() - started, 0.2)
        self.assertEqual(bot.room.send_text.call_count, 2)

    def test_a_send_after_the_interval_has_passed_is_not_delayed(self):
        bot = _bot(min_send_interval=0.05)
        bot.send_text("one")
        time.sleep(0.06)
        started = time.monotonic()
        bot.send_text("two")
        self.assertLess(time.monotonic() - started, 0.05)

    def test_an_interval_of_zero_disables_pacing(self):
        bot = _bot(min_send_interval=0)
        started = time.monotonic()
        for _ in range(5):
            bot.send_text("x")
        self.assertLess(time.monotonic() - started, 0.2)
        self.assertEqual(bot.room.send_text.call_count, 5)

    def test_concurrent_senders_are_serialised(self):
        """Two threads that each waited must not then send together."""
        bot = _bot(min_send_interval=0.1)
        times = []
        bot.room.send_text.side_effect = lambda text: times.append(time.monotonic())
        threads = [threading.Thread(target=bot.send_text, args=(f"m{i}",))
                   for i in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        self.assertEqual(len(times), 3)
        gaps = [b - a for a, b in zip(sorted(times), sorted(times)[1:])]
        for gap in gaps:
            self.assertGreaterEqual(gap, 0.09, f"sends overlapped: {gaps}")

    def test_the_return_value_reaches_the_caller(self):
        bot = _bot(min_send_interval=0)
        bot.room.send_text.return_value = {"event_id": "$abc"}
        self.assertEqual(bot.send_text("x"), {"event_id": "$abc"})


class TestSlowSendIsReported(unittest.TestCase):

    def test_a_send_the_server_holds_logs_a_warning(self):
        bot = _bot(min_send_interval=0)
        bot.room.send_text.side_effect = lambda text: time.sleep(0.05)
        lines = []
        with patch.object(matrixapi, "SLOW_SEND_WARNING_SECONDS", 0.01), \
                patch.object(matrixapi.LOG, "warning", side_effect=lines.append):
            bot.send_text("held")
        self.assertTrue(lines, "a held send logged nothing")
        self.assertIn("rate limit", lines[0])

    def test_a_prompt_send_logs_no_warning(self):
        bot = _bot(min_send_interval=0)
        lines = []
        with patch.object(matrixapi.LOG, "warning", side_effect=lines.append):
            bot.send_text("quick")
        self.assertEqual(lines, [])

    def test_a_raising_send_still_records_the_time_and_releases_the_lock(self):
        bot = _bot(min_send_interval=0)
        bot.room.send_text.side_effect = RuntimeError("boom")
        with self.assertRaises(RuntimeError):
            bot.send_text("x")
        self.assertGreater(bot._last_send, 0.0)
        self.assertFalse(bot._send_lock.locked())


if __name__ == "__main__":
    unittest.main()
