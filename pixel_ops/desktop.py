"""Per-user Windows desktop lifecycle. No game or provider responsibilities."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import logging
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser

import psutil

ROOT = Path(__file__).resolve().parents[1]
STUDIO_URL = "http://127.0.0.1:5174"


class DesktopManager:
    def __init__(self, root: Path = ROOT):
        self.root = root.resolve()
        self.state_dir = self.root / "pixel_ops/cache/desktop"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def lock(self, name="control", timeout=15):
        import msvcrt
        with (self.state_dir / f"{name}.lock").open("a+b") as handle:
            handle.seek(0, 2)
            if not handle.tell():
                handle.write(b"0")
                handle.flush()
            deadline = time.monotonic() + timeout
            while True:
                try:
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Pixel OPs controller is already busy")
                    time.sleep(.1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)

    def _path(self, kind):
        return self.state_dir / f"{kind}.json"

    def _matches(self, process, kind):
        try:
            args = [a.replace("\\", "/").lower() for a in process.cmdline()]
            cwd = Path(process.cwd()).resolve()
            root = self.root.as_posix().lower()
            if kind == "display":
                return any(a == root + "/pixel_ops/main.py" or (a == "pixel_ops/main.py" and cwd == self.root) for a in args)
            if kind == "studio":
                return any("vite/bin/vite.js" in a and (root + "/config-studio/" in a or cwd == self.root / "config-studio") for a in args)
            return "pixel_ops.desktop" in args and "run-desktop" in args and cwd == self.root
        except (psutil.Error, OSError):
            return False

    def _record(self, kind, process):
        data = {"pid": process.pid, "created_at": process.create_time()}
        path = self._path(kind)
        temporary = path.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(json.dumps(data), encoding="utf-8")
        temporary.replace(path)
        if kind == "display":
            (self.root / "pixel_ops/output/runtime.pid").write_text(str(process.pid))
        return process

    def process(self, kind):
        try:
            data = json.loads(self._path(kind).read_text())
            process = psutil.Process(int(data["pid"]))
            if abs(process.create_time() - float(data["created_at"])) < .01 and self._matches(process, kind):
                return process
        except (psutil.Error, OSError, ValueError, TypeError, KeyError):
            pass
        # Adopt existing repo-local processes started by Studio or a terminal.
        for process in psutil.process_iter():
            if self._matches(process, kind):
                return process
        return None

    def status(self):
        result = {}
        for kind in ("desktop", "display", "studio"):
            process = self.process(kind)
            result[kind] = {"running": process is not None, "pid": process.pid if process else None}
        return result

    def _spawn(self, kind, args, cwd):
        output = self.root / "pixel_ops/output"
        output.mkdir(parents=True, exist_ok=True)
        env = {**os.environ, "PIXEL_OPS_TRAY": "1", "PYTHONUNBUFFERED": "1"}
        if kind in ("desktop", "display"):
            windowless = Path(sys.executable).with_name("pythonw.exe")
            if not windowless.exists():
                raise RuntimeError("This Python installation is missing pythonw.exe for windowless launch")
            args = [str(windowless), *args[1:]]
        with (output / f"{kind}.log").open("ab") as log:
            child = subprocess.Popen(args, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                     stdout=log, stderr=log,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
        return self._record(kind, psutil.Process(child.pid))

    def start(self, kind):
        with self.lock():
            existing = self.process(kind)
            if existing:
                return self._record(kind, existing)
            if kind == "display":
                return self._spawn(kind, [sys.executable, str(self.root / "pixel_ops/main.py"), "--forever"], self.root)
            if kind == "desktop":
                return self._spawn(kind, [sys.executable, "-m", "pixel_ops.desktop", "run-desktop"], self.root)
            vite = self.root / "config-studio/node_modules/vite/bin/vite.js"
            node = shutil.which("node")
            if not vite.exists() or not node:
                raise RuntimeError("Install Node.js and run npm ci in config-studio first")
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", 5174)) == 0:
                    raise RuntimeError("Port 5174 belongs to another process; refusing to start a duplicate Studio")
            return self._spawn(kind, [node, str(vite), "--host", "127.0.0.1", "--port", "5174", "--strictPort"], vite.parents[3])

    def stop(self, kind):
        with self.lock():
            process = self.process(kind)
            if not process:
                return
            protected = set()
            if kind == "studio":
                display = self.process("display")
                if display:
                    protected = {display.pid, *(p.pid for p in display.children(recursive=True))}
            targets = [p for p in process.children(recursive=True) if p.pid not in protected]
            targets.append(process)
            for target in reversed(targets):
                try:
                    target.terminate()
                except psutil.NoSuchProcess:
                    pass
            _, alive = psutil.wait_procs(targets, timeout=5)
            if alive:
                raise RuntimeError(f"Could not stop {kind}; inspect pixel_ops/output/desktop.log")
            self._path(kind).unlink(missing_ok=True)
            if kind == "display":
                (self.root / "pixel_ops/output/runtime.pid").unlink(missing_ok=True)

    def wait_studio(self, timeout=45):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                if self.process("studio"):
                    with urllib.request.urlopen(STUDIO_URL + "/api/runtime/status", timeout=1) as response:
                        if response.status == 200:
                            return
            except (urllib.error.URLError, OSError):
                pass
            time.sleep(.3)
        raise RuntimeError("Config Studio did not become ready; inspect pixel_ops/output/studio.log")

    def request_exit(self):
        process = self.process("desktop")
        if not process:
            self.stop("studio")
            self.stop("display")
            return
        (self.state_dir / "exit.json").write_text(json.dumps({"pid": process.pid, "created_at": process.create_time()}))
        try:
            process.wait(timeout=60)
        except psutil.TimeoutExpired as error:
            raise RuntimeError("Tray shutdown is taking too long; inspect desktop.log") from error


def run_tray(manager):
    import pystray
    from PIL import Image
    with manager.lock("tray", timeout=0):
        manager._record("desktop", psutil.Process())
        identity = json.loads(manager._path("desktop").read_text())
        exit_path = manager.state_dir / "exit.json"
        exit_path.unlink(missing_ok=True)
        shutdown = threading.Event()
        operation = threading.Lock()
        image = Image.open(manager.root / "config-studio/public/favicon.ico").convert("RGBA")

        def action(name):
            def execute(icon, item):
                def worker():
                    with operation:
                        if shutdown.is_set():
                            return
                        try:
                            pwsh = shutil.which("pwsh")
                            if not pwsh:
                                raise RuntimeError("PowerShell Core (pwsh) is required")
                            result = subprocess.run([pwsh, "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-File",
                                                     str(manager.root / "tools/windows/PixelOps.ps1"), "-Action", name],
                                                    cwd=manager.root, creationflags=subprocess.CREATE_NO_WINDOW,
                                                    capture_output=True, text=True, timeout=55)
                            if result.returncode:
                                raise RuntimeError(result.stderr.strip())
                            icon.title = "Pixel OPs"
                        except Exception:
                            logging.exception("Tray action %s failed", name)
                            icon.title = f"Pixel OPs: {name} failed (see desktop.log)"
                threading.Thread(target=worker, daemon=True).start()
            return execute

        icon = pystray.Icon("pixel-ops", image, "Pixel OPs", menu=pystray.Menu(
            pystray.MenuItem("Open Config Studio", action("OpenStudio"), default=True),
            pystray.MenuItem("Stop Config Studio", action("StopStudio")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Restart display", action("RestartDisplay")),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", lambda icon, item: shutdown.set()),
        ))

        def watch():
            while not shutdown.wait(.3):
                try:
                    if json.loads(exit_path.read_text()) == identity:
                        shutdown.set()
                except (OSError, ValueError):
                    pass
            with operation:
                for kind in ("studio", "display"):
                    try:
                        manager.stop(kind)
                    except Exception:
                        logging.exception("Desktop shutdown failed for %s", kind)
                icon.stop()

        def setup(icon):
            icon.visible = True
            try:
                # Adopt a pre-tray setup by reopening its display with tray mode
                # enabled. Later Start calls reuse this singleton controller.
                manager.stop("display")
                manager.start("display")
            except Exception:
                logging.exception("Display startup failed")
                icon.title = "Pixel OPs: display unavailable (see desktop.log)"
            threading.Thread(target=watch, daemon=True).start()
        try:
            icon.run(setup=setup)
        finally:
            manager._path("desktop").unlink(missing_ok=True)
            exit_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["status", "start-desktop", "run-desktop", "exit", "start-display", "stop-display", "restart-display", "start-studio", "run-studio", "stop-studio", "wait-studio", "open-browser"])
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("The desktop controller currently supports Windows only")
    manager = DesktopManager()
    output = ROOT / "pixel_ops/output"
    output.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=output / "desktop.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        if args.action == "run-desktop":
            existing = manager.process("desktop")
            own_tree = {os.getpid(), *(p.pid for p in psutil.Process().parents())}
            if existing and existing.pid not in own_tree:
                # A manually started tray may precede task registration. Let
                # the task attach to its lifetime rather than create an icon.
                existing.wait()
            else:
                run_tray(manager)
        elif args.action == "status":
            print(json.dumps(manager.status()))
        elif args.action == "exit":
            manager.request_exit()
        elif args.action == "wait-studio":
            manager.wait_studio()
        elif args.action == "open-browser":
            manager.wait_studio()
            webbrowser.open(STUDIO_URL)
        elif args.action == "run-studio":
            process = manager.start("studio")
            try:
                process.wait()
            except psutil.NoSuchProcess:
                pass
        else:
            verb, kind = args.action.split("-", 1)
            if verb in ("stop", "restart"):
                manager.stop(kind)
            if verb in ("start", "restart"):
                manager.start(kind)
        return 0
    except Exception as error:
        logging.exception("Desktop action failed: %s", args.action)
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
