"""Small Linux init for the isolated check; never loads the model or application."""
from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def child_pids() -> list[int]:
    """Only our direct children, including descendants adopted by the subreaper."""
    path = Path(f'/proc/self/task/{os.getpid()}/children')
    with path.open(encoding='ascii') as stream:
        data = stream.read(4097)
    if len(data) > 4096 or any(not word.isdecimal() for word in data.split()):
        raise RuntimeError('child_inventory_invalid')
    return [int(word) for word in data.split()]


def send(pid: int, signum: int, *, group: bool = False) -> None:
    try:
        (os.killpg if group else os.kill)(pid, signum)
    except ProcessLookupError:
        pass  # A child can exit between its inventory and signal delivery.


def supervise(command: list[str], *, grace_seconds: float = 6.0) -> int:
    """Forward shutdown, reap children, and fail if a probe leaves live descendants."""
    if sys.platform != 'linux' or not 0 < grace_seconds <= 6:
        raise RuntimeError('launcher_platform_or_grace_invalid')
    # PR_SET_CHILD_SUBREAPER also supports checks run beneath Docker's optional init.
    if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) != 0:
        raise RuntimeError('subreaper_failed')
    requested: list[int] = []
    child: subprocess.Popen | None = None

    def shutdown(signum: int, _frame: object) -> None:
        if not requested:
            requested.append(signum)
        if child is not None:
            send(child.pid, signum, group=True)

    old = {s: signal.signal(s, shutdown) for s in (signal.SIGTERM, signal.SIGINT)}
    try:
        child = subprocess.Popen(command, close_fds=True, start_new_session=True)
        if requested:
            send(child.pid, requested[0], group=True)
        main_status: int | None = None
        deadline: float | None = None
        while main_status is None:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
            except InterruptedError:
                continue
            if pid == child.pid:
                main_status = os.waitstatus_to_exitcode(status)
                child.returncode = main_status
                break
            if requested and deadline is None:
                deadline = time.monotonic() + grace_seconds
            if deadline is not None and time.monotonic() >= deadline:
                send(child.pid, signal.SIGKILL, group=True)
            time.sleep(.02)

        # A successful probe must reap its own live children. Kill any leak and
        # report failure rather than leaving it to implicit container teardown.
        leaked = bool(child_pids())
        cleanup_deadline = time.monotonic() + 2
        while True:
            for pid in child_pids():
                send(pid, signal.SIGKILL)
            while True:
                try:
                    pid, _status = os.waitpid(-1, os.WNOHANG)
                except ChildProcessError:
                    pid = 0
                if pid == 0:
                    break
            if not child_pids():
                break
            if time.monotonic() >= cleanup_deadline:
                raise RuntimeError('launcher_cleanup_failed')
            time.sleep(.02)
        if requested:
            return 128 + requested[0]
        if leaked:
            return 125
        return main_status if main_status >= 0 else 128 - main_status
    finally:
        if child is not None and child.returncode is None:
            send(child.pid, signal.SIGKILL, group=True)
            child.wait(timeout=2)
        for signum, handler in old.items():
            signal.signal(signum, handler)


def main() -> int:
    args = sys.argv[1:]
    if args not in ([], ['--preflight-only'], ['--diagnostic-only']):
        return 2
    try:
        return supervise([sys.executable, '-I', '-B', '/app/scripts/news_ner_cloud_probe.py', *args])
    except Exception as error:
        print(json.dumps({'schema': 'lanes-ner-cloud-launcher-v1', 'event': 'failed',
                          'error_code': 'launcher_failed', 'error_type': type(error).__name__}), flush=True)
        return 125


if __name__ == '__main__':
    raise SystemExit(main())
