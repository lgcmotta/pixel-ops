"""Account-only Codex bridge. No thread methods or conversation content."""
from __future__ import annotations

import argparse
import json
import math
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from pixel_ops.data_sources.ai_quota import AIQuotaSnapshot, AIQuotaWindow

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HOME = ROOT / "pixel_ops/cache/codex_account"


def resolve_executable(executable: str = "codex") -> str:
    """Scheduled tasks do not inherit the Codex desktop app's injected PATH."""
    binary = shutil.which(executable)
    if binary and Path(binary).suffix.lower() not in (".cmd", ".bat"):
        return binary
    if sys.platform == "win32" and executable.lower() in ("codex", "codex.exe"):
        local = os.environ.get("LOCALAPPDATA")
        if local:
            installed = Path(local) / "OpenAI/Codex/bin"
            try:
                candidates = sorted(installed.glob("*/codex.exe"), key=lambda path: path.stat().st_mtime, reverse=True)
                if candidates:
                    return str(candidates[0])
            except OSError:
                pass
    raise FileNotFoundError("Codex CLI not found; configure its native executable path")


def profile_path(value: str = "") -> Path:
    candidate = Path(value).expanduser() if value else DEFAULT_HOME
    return (ROOT / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()


@contextmanager
def profile_lock(home: Path, timeout: float = 15):
    """OS-backed cross-process lock, automatically released after a crash."""
    home.mkdir(parents=True, exist_ok=True)
    with (home / ".account.lock").open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        deadline = time.monotonic() + timeout
        while True:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Account profile is busy; sign-in may be in progress") from None
                time.sleep(0.05)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


class AccountRPC:
    def __init__(self, home: Path, executable: str = "codex", timeout: float = 15, deadline: float | None = None):
        self.timeout = timeout
        self.sequence = 0
        self.deadline = deadline
        self.messages = queue.Queue()
        self.notifications = []
        binary = resolve_executable(executable)
        env = dict(os.environ, CODEX_HOME=str(home))
        for name in ("OPENAI_API_KEY", "CODEX_ACCESS_TOKEN"):
            env.pop(name, None)
        # No model execution and no dependence on the coding client's config.
        self.process = subprocess.Popen(
            [binary, "app-server", "--stdio", "-c", 'cli_auth_credentials_store="file"'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", env=env, cwd=home,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()
        try:
            self.call("initialize", {"clientInfo": {"name": "pixel_ops_account", "version": "1.0"}})
            self.send({"method": "initialized"})
        except Exception:
            self.close()
            raise

    def _read(self):
        try:
            for line in self.process.stdout:
                try:
                    self.messages.put(json.loads(line))
                except ValueError:
                    continue
        finally:
            self.messages.put(None)

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def call(self, method: str, params=None):
        allowed = {"initialize", "account/read", "account/login/start", "account/login/cancel", "account/logout", "account/rateLimits/read", "account/usage/read"}
        if method not in allowed:
            raise ValueError("Method is outside the account-only contract")
        self.sequence += 1
        request_id = self.sequence
        self.send({"id": request_id, "method": method, "params": params or {}})
        deadline = min(time.monotonic() + self.timeout, self.deadline or float("inf"))
        while True:
            try:
                message = self.messages.get(timeout=max(0.001, deadline - time.monotonic()))
            except queue.Empty:
                raise TimeoutError("Codex account request timed out") from None
            if message is None:
                raise ConnectionError("Codex account process exited")
            if message.get("id") == request_id and ("result" in message or "error" in message):
                if "error" in message:
                    # Never propagate arbitrary server payloads into logs or HTTP.
                    raise RuntimeError(f"Codex account method unavailable: {method}")
                return message["result"]
            if "method" in message and "id" not in message:
                self.notifications.append(message)
            if time.monotonic() >= deadline:
                raise TimeoutError("Codex account request timed out")

    def drain(self):
        result, self.notifications = self.notifications, []
        while True:
            try:
                message = self.messages.get_nowait()
            except queue.Empty:
                break
            if message is None:
                raise ConnectionError("Codex account process exited")
            result.append(message)
        return result

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=2)
        for stream in (self.process.stdin, self.process.stdout):
            if stream:
                stream.close()


def normalize_limits(limits: dict, account: dict, usage: dict, now: datetime, stale_seconds: int = 180) -> AIQuotaSnapshot:
    buckets = limits.get("rateLimitsByLimitId")
    if not isinstance(buckets, dict) or not buckets:
        single = limits.get("rateLimits") or {}
        buckets = {single.get("limitId") or "codex": single}
    windows = []
    for bucket_id, bucket in sorted(buckets.items()):
        if not isinstance(bucket, dict):
            continue
        for position in ("primary", "secondary"):
            window = bucket.get(position)
            if not isinstance(window, dict):
                continue
            try:
                percent = float(window["usedPercent"])
                minutes = int(window["windowDurationMins"])
                reset = window.get("resetsAt")
                reset_at = datetime.fromtimestamp(float(reset), timezone.utc) if reset is not None else None
                if not math.isfinite(percent) or not 0 <= percent <= 100 or minutes <= 0:
                    continue
            except (KeyError, TypeError, ValueError, OverflowError, OSError):
                continue
            windows.append(AIQuotaWindow(str(bucket_id), str(bucket.get("limitName") or bucket_id), minutes, percent, reset_at))
    daily = tuple((str(row["startDate"]), int(row["tokens"])) for row in (usage.get("dailyUsageBuckets") or [])
                  if isinstance(row, dict) and isinstance(row.get("tokens"), int) and row.get("startDate"))
    total = (usage.get("summary") or {}).get("lifetimeTokens")
    return AIQuotaSnapshot("codex", tuple(windows), now, "ok" if windows else "unavailable",
                           str(account.get("email") or "Connected account"), str(account.get("planType") or ""),
                           daily, total if isinstance(total, int) else None, stale_seconds)


def public_snapshot(snapshot: AIQuotaSnapshot) -> dict:
    from dataclasses import asdict
    value = asdict(snapshot)
    value["observed_at"] = snapshot.observed_at.isoformat() if snapshot.observed_at else None
    for item, window in zip(value["windows"], snapshot.windows):
        item["reset_at"] = window.reset_at.isoformat() if window.reset_at else None
    return value


class CodexAccountSource:
    def __init__(self, account_home="", executable="codex", poll_seconds=60, timeout_seconds=15, stale_seconds=180):
        self.home = profile_path(account_home)
        self.executable = executable
        self.poll_seconds = max(30, int(poll_seconds))
        self.timeout = max(1, float(timeout_seconds))
        self.stale_seconds = max(60, int(stale_seconds))
        self._active_rpc = None
        self._closed = False

    def close(self):
        self._closed = True
        if self._active_rpc:
            self._active_rpc.close()

    def current(self, now=None):
        now = now or datetime.now(timezone.utc)
        if self._closed:
            return AIQuotaSnapshot("codex", status="unavailable")
        deadline = time.monotonic() + self.timeout
        try:
            with profile_lock(self.home, self.timeout):
                rpc = AccountRPC(self.home, self.executable, self.timeout, deadline=deadline)
                self._active_rpc = rpc
                try:
                    account = rpc.call("account/read", {"refreshToken": False}).get("account")
                    if not account or account.get("type") != "chatgpt":
                        return AIQuotaSnapshot("codex", status="disconnected", stale_seconds=self.stale_seconds)
                    limits = rpc.call("account/rateLimits/read")
                    try:
                        usage = rpc.call("account/usage/read")
                    except (RuntimeError, TimeoutError):
                        usage = {}
                    snapshot = normalize_limits(limits, account, usage, now, self.stale_seconds)
                finally:
                    rpc.close()
                    self._active_rpc = None
                cache = self.home / "quota.json"
                temporary = cache.with_suffix(".tmp")
                temporary.write_text(json.dumps(public_snapshot(snapshot)), encoding="utf-8")
                temporary.replace(cache)
                return snapshot
        except (OSError, RuntimeError, TimeoutError, ValueError, ConnectionError):
            # Retain the true last-success timestamp; failure is never fresh quota.
            try:
                value = json.loads((self.home / "quota.json").read_text(encoding="utf-8"))
                windows = tuple(AIQuotaWindow(**{**row, "reset_at": datetime.fromisoformat(row["reset_at"]) if row.get("reset_at") else None}) for row in value["windows"])
                observed = datetime.fromisoformat(value["observed_at"])
                status = "ok" if 0 <= (now - observed).total_seconds() <= self.stale_seconds else "stale"
                return AIQuotaSnapshot("codex", windows, observed, status, value.get("account", ""), value.get("plan", ""), stale_seconds=self.stale_seconds)
            except (OSError, ValueError, KeyError, TypeError):
                return AIQuotaSnapshot("codex", status="unavailable", stale_seconds=self.stale_seconds)


class AccountController:
    """Studio-owned sign-in session, sharing the runtime's OS profile lock."""
    def __init__(self, source):
        self.source = source
        self.rpc = None
        self.lock = None
        self.login = None
        self.expires = 0.0

    def close(self):
        if self.rpc:
            self.rpc.close()
            self.rpc = None
        if self.lock:
            self.lock.__exit__(None, None, None)
            self.lock = None

    def handle(self, method, params):
        if method == "login/start":
            self.close()
            lock = profile_lock(self.source.home, self.source.timeout)
            lock.__enter__()
            self.lock = lock
            try:
                self.rpc = AccountRPC(self.source.home, self.source.executable, self.source.timeout)
                kind = "chatgptDeviceCode" if params.get("flow") == "device" else "chatgpt"
                result = self.rpc.call("account/login/start", {"type": kind})
                self.login = {key: result[key] for key in ("loginId", "authUrl", "verificationUrl", "userCode") if key in result}
                self.login["status"] = "pending"
                self.expires = time.monotonic() + 600
                return self.login
            except Exception:
                self.close()
                raise
        if method == "login/status":
            if self.rpc:
                for message in self.rpc.drain():
                    if message.get("method") == "account/login/completed":
                        completed = message.get("params") or {}
                        self.login = {"status": "connected" if completed.get("success") else "failed"}
                        self.close()
                        break
                if self.rpc and time.monotonic() >= self.expires:
                    self.login = {"status": "expired"}
                    self.close()
            return self.login or {"status": "idle"}
        if method == "login/cancel":
            try:
                if self.rpc and self.login:
                    self.rpc.call("account/login/cancel", {"loginId": self.login.get("loginId")})
            finally:
                self.close()
                self.login = {"status": "cancelled"}
            return self.login
        if method == "disconnect":
            self.close()
            with profile_lock(self.source.home, self.source.timeout):
                rpc = AccountRPC(self.source.home, self.source.executable, self.source.timeout)
                try:
                    rpc.call("account/logout")
                    (self.source.home / "quota.json").unlink(missing_ok=True)
                finally:
                    rpc.close()
            return {"status": "disconnected"}
        if method in ("status", "refresh"):
            if self.rpc:
                return {"status": "connecting"}
            return public_snapshot(self.source.current())
        raise ValueError("Unknown account action")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", default="")
    parser.add_argument("--executable", default="codex")
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    controller = AccountController(CodexAccountSource(args.home, args.executable))
    try:
        if not args.serve:
            print(json.dumps(controller.handle("status", {})))
            return
        for line in sys.stdin:
            request = {}
            try:
                request = json.loads(line)
                result = controller.handle(request["method"], request.get("params") or {})
                response = {"id": request.get("id"), "result": result}
            except Exception as error:
                controller.close()
                response = {"id": request.get("id"), "error": f"Account connection failed ({type(error).__name__}). Check the Codex executable, connection and sign-in."}
            print(json.dumps(response), flush=True)
    finally:
        controller.close()


if __name__ == "__main__":
    main()
