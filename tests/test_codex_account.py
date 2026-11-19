import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from pixel_ops.data_sources.ai_quota import AIQuotaSnapshot
from pixel_ops.data_sources.codex_account import AccountController, AccountRPC, CodexAccountSource, normalize_limits, profile_lock, public_snapshot


NOW = datetime(2026, 10, 29, tzinfo=timezone.utc)
LIMITS = {"rateLimitsByLimitId": {
    "codex": {"primary": {"usedPercent": 25, "windowDurationMins": 300, "resetsAt": int((NOW + timedelta(hours=2)).timestamp())}},
    "other": {"limitName": "Other", "primary": {"usedPercent": 40, "windowDurationMins": 10080}},
}}


class FakeRPC:
    results = {}
    notifications = []
    fail = None
    calls = []

    def __init__(self, *args, **kwargs):
        if self.fail:
            raise self.fail

    def call(self, method, params=None):
        self.calls.append((method, params))
        result = self.results.get(method, {})
        if isinstance(result, Exception):
            raise result
        return result

    def drain(self):
        result, type(self).notifications = self.notifications, []
        return result

    def close(self):
        pass


class CodexAccountTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.source = CodexAccountSource(str(self.home))
        FakeRPC.fail = None
        FakeRPC.calls = []
        FakeRPC.notifications = []
        FakeRPC.results = {
            "account/read": {"account": {"type": "chatgpt", "email": "test@example.test", "planType": "pro"}},
            "account/rateLimits/read": LIMITS,
            "account/usage/read": {"summary": {"lifetimeTokens": 150}, "dailyUsageBuckets": [{"startDate": "2026-10-29", "tokens": 100}]},
            "account/login/start": {"loginId": "login", "authUrl": "https://auth.openai.com/test"},
        }
        self.addCleanup(self.tmp.cleanup)

    def test_multibucket_windows_and_account_totals(self):
        with patch("pixel_ops.data_sources.codex_account.AccountRPC", FakeRPC):
            snapshot = self.source.current(NOW)
        self.assertEqual([window.bucket for window in snapshot.windows], ["codex", "other"])
        self.assertEqual(snapshot.windows[0].remaining(NOW), 75)
        self.assertEqual(snapshot.lifetime_tokens, 150)
        self.assertEqual(snapshot.daily_tokens, (("2026-10-29", 100),))
        self.assertFalse(any(method.startswith("thread/") for method, _ in FakeRPC.calls))
        self.assertEqual(json.loads((self.home / "quota.json").read_text())["observed_at"], NOW.isoformat())

    def test_missing_optional_usage_does_not_hide_quota(self):
        FakeRPC.results["account/usage/read"] = RuntimeError("Unsupported")
        with patch("pixel_ops.data_sources.codex_account.AccountRPC", FakeRPC):
            snapshot = self.source.current(NOW)
        self.assertEqual(snapshot.status, "ok")
        self.assertIsNone(snapshot.lifetime_tokens)
        self.assertEqual(snapshot.daily_tokens, ())

    def test_reset_boundary_and_staleness_never_imply_refill(self):
        snapshot = normalize_limits(LIMITS, {}, {}, NOW)
        self.assertIsNone(snapshot.windows[0].remaining(NOW + timedelta(hours=2)))
        self.assertTrue(snapshot.fresh(NOW + timedelta(seconds=180)))
        self.assertFalse(snapshot.fresh(NOW + timedelta(seconds=181)))

    def test_single_bucket_and_invalid_windows(self):
        snapshot = normalize_limits({"rateLimits": {"primary": {"usedPercent": float("nan"), "windowDurationMins": 300},
                                                           "secondary": {"usedPercent": 20, "windowDurationMins": 10080}}}, {}, {}, NOW)
        self.assertEqual(len(snapshot.windows), 1)
        self.assertEqual(snapshot.windows[0].window_minutes, 10080)

    def test_failures_keep_true_last_success_timestamp(self):
        with patch("pixel_ops.data_sources.codex_account.AccountRPC", FakeRPC):
            self.source.current(NOW)
            FakeRPC.fail = TimeoutError()
            recent = self.source.current(NOW + timedelta(seconds=90))
            stale = self.source.current(NOW + timedelta(seconds=181))
        self.assertTrue(recent.fresh(NOW + timedelta(seconds=90)))
        self.assertEqual(stale.status, "stale")
        self.assertEqual(stale.observed_at, NOW)

    def test_missing_cli_is_unavailable(self):
        with patch("pixel_ops.data_sources.codex_account.resolve_executable", side_effect=FileNotFoundError()):
            snapshot = self.source.current(NOW)
        self.assertEqual(snapshot.status, "unavailable")
        self.assertIsNone(snapshot.observed_at)

    def test_real_stdio_framing_and_timeout_cleanup(self):
        script = self.home / "fake_server.py"
        script.write_text('''import json, sys, time
for line in sys.stdin:
 request=json.loads(line)
 if request.get('method')=='initialized': continue
 if request.get('method')=='account/read':
  print(json.dumps({'method':'account/updated','params':{'authMode':'chatgpt'}}),flush=True)
 result={} if request['method']=='initialize' else {'account':{'type':'chatgpt'}}
 print(json.dumps({'id':request['id'],'result':result}),flush=True)
''')
        real_popen = subprocess.Popen
        children = []
        def spawn(_args, **kwargs):
            child = real_popen([sys.executable, str(script)], **kwargs)
            children.append(child)
            return child
        with patch("pixel_ops.data_sources.codex_account.shutil.which", return_value=sys.executable), patch("pixel_ops.data_sources.codex_account.subprocess.Popen", side_effect=spawn):
            rpc = AccountRPC(self.home, timeout=2)
            self.assertEqual(rpc.call("account/read")["account"]["type"], "chatgpt")
            self.assertEqual(rpc.drain()[0]["method"], "account/updated")
            with self.assertRaises(ValueError):
                rpc.call("thread/start")
            rpc.close()
            script.write_text("import time; time.sleep(5)")
            with self.assertRaises(TimeoutError):
                AccountRPC(self.home, timeout=0.1)
        self.assertTrue(all(child.poll() is not None for child in children))

    def test_api_key_is_not_subscription_connection(self):
        FakeRPC.results["account/read"] = {"account": {"type": "apiKey"}}
        with patch("pixel_ops.data_sources.codex_account.AccountRPC", FakeRPC):
            self.assertEqual(self.source.current(NOW).status, "disconnected")
        self.assertFalse(any(method == "account/rateLimits/read" for method, _ in FakeRPC.calls))

    def test_browser_login_success_and_persistence(self):
        controller = AccountController(self.source)
        self.addCleanup(controller.close)
        with patch("pixel_ops.data_sources.codex_account.AccountRPC", FakeRPC):
            started = controller.handle("login/start", {})
            self.assertEqual(started["status"], "pending")
            self.assertEqual(FakeRPC.calls[-1][1]["type"], "chatgpt")
            FakeRPC.notifications = [{"method": "account/login/completed", "params": {"success": True}}]
            self.assertEqual(controller.handle("login/status", {})["status"], "connected")
            self.assertIsNone(controller.rpc)
            self.assertEqual(controller.handle("status", {})["account"], "test@example.test")
            self.assertEqual(CodexAccountSource(str(self.home)).home, self.home)

    def test_device_code_cancel_expire_and_failure(self):
        controller = AccountController(self.source)
        self.addCleanup(controller.close)
        with patch("pixel_ops.data_sources.codex_account.AccountRPC", FakeRPC):
            controller.handle("login/start", {"flow": "device"})
            self.assertEqual(FakeRPC.calls[-1][1]["type"], "chatgptDeviceCode")
            self.assertEqual(controller.handle("login/cancel", {})["status"], "cancelled")
            controller.handle("login/start", {})
            controller.expires = 0
            self.assertEqual(controller.handle("login/status", {})["status"], "expired")
            controller.handle("login/start", {})
            FakeRPC.notifications = [{"method": "account/login/completed", "params": {"success": False, "error": "sensitive internal payload"}}]
            self.assertEqual(controller.handle("login/status", {}), {"status": "failed"})

    def test_disconnect_deletes_only_sanitized_profile_cache(self):
        (self.home / "quota.json").write_text("{}")
        controller = AccountController(self.source)
        with patch("pixel_ops.data_sources.codex_account.AccountRPC", FakeRPC):
            self.assertEqual(controller.handle("disconnect", {})["status"], "disconnected")
        self.assertFalse((self.home / "quota.json").exists())
        self.assertIn(("account/logout", None), FakeRPC.calls)

    def test_profile_lock_is_exclusive_and_releases(self):
        with profile_lock(self.home):
            with self.assertRaises(TimeoutError):
                with profile_lock(self.home, 0.01):
                    pass
        with profile_lock(self.home, 0.01):
            pass

    def test_quota_dto_is_immutable_and_sanitized(self):
        snapshot = AIQuotaSnapshot("codex")
        with self.assertRaises(AttributeError):
            snapshot.status = "ok"
        self.assertNotIn("token", public_snapshot(snapshot))


if __name__ == "__main__":
    unittest.main()
