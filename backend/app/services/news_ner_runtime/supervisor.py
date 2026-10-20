"""One bounded subprocess session; no Docker, ORM, network or automatic retry."""
from __future__ import annotations

import asyncio
import contextlib
import os
from pathlib import Path
import signal
import sys
import time

from .protocol import (CLEANUP_SECONDS, COLD_SECONDS, INPUT_BYTES, REQUEST_SECONDS, SESSION_SECONDS,
                       VERSION, decode, encode, validate_request, verify_result)
from app.services.news_ner.contract import MAX_OUTPUT_BYTES


class RuntimeFailure(RuntimeError):
    """Stable public code only; private subprocess diagnostics are never interpolated."""


class Session:
    def __init__(self, bundle_sha: str, code: dict, *, worker: Path | None = None) -> None:
        self.bundle_sha = bundle_sha
        self.code = code
        self.worker = worker or Path(__file__).with_name('worker.py')
        self.state = 'new'
        self.proc: asyncio.subprocess.Process | None = None
        self.started = time.monotonic()
        self.busy = False
        self.ready: dict = {}
        self.cleanup_seconds: float | None = None

    async def _exchange(self, message: dict, timeout: float) -> dict:
        assert self.proc is not None and self.proc.stdin is not None and self.proc.stdout is not None
        async def exchange() -> dict:
            self.proc.stdin.write(encode(message, INPUT_BYTES))
            await self.proc.stdin.drain()
            data = await self.proc.stdout.readline()
            if not data:
                raise RuntimeFailure('worker_exit')
            value = decode(data)
            if value.get('state') == 'error':
                raise RuntimeFailure('worker_error')
            return value
        try:
            return await asyncio.wait_for(exchange(), timeout)
        except asyncio.TimeoutError:
            raise RuntimeFailure('deadline') from None
        except (ValueError, BrokenPipeError, ConnectionError):
            raise RuntimeFailure('invalid_worker_message') from None

    async def start(self) -> dict:
        if self.state != 'new':
            raise RuntimeFailure('invalid_state')
        self.state = 'startup'
        # Fixed allowlist: credentials/proxies/PYTHONPATH/loader variables are absent.
        env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'LANG': 'C.UTF-8', 'HOME': '/nonexistent',
               'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
               'CUDA_VISIBLE_DEVICES': '', 'PYTHONDONTWRITEBYTECODE': '1'}
        try:
            self.proc = await asyncio.create_subprocess_exec(sys.executable, '-I', '-B', str(self.worker),
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                env=env, close_fds=True, start_new_session=True, limit=MAX_OUTPUT_BYTES)
            self.ready = await self._exchange({'state': 'startup', 'bundle_sha256': self.bundle_sha, 'code': self.code}, COLD_SECONDS)
            if self.ready.get('state') != 'ready' or self.ready.get('runtime') != VERSION or self.ready.get('isolation', {}).get('raw_socket_denied') is not True:
                raise RuntimeFailure('invalid_readiness')
            self.state = 'ready'
            return self.ready
        except BaseException:
            self.state = 'failed'
            await self.close()
            raise

    async def request(self, request: dict, *, timeout: float = REQUEST_SECONDS) -> dict:
        if self.busy:
            raise RuntimeFailure('concurrent_request')
        if self.state != 'ready':
            raise RuntimeFailure('not_ready')
        if not 0 < timeout <= REQUEST_SECONDS or time.monotonic() - self.started + timeout + CLEANUP_SECONDS > SESSION_SECONDS:
            raise RuntimeFailure('session_budget')
        validate_request(request)
        self.busy = True
        self.state = 'request'
        request_started = time.monotonic()
        try:
            response = await self._exchange({'state': 'request', 'request': request}, timeout)
            if set(response) != {'state', 'record_id', 'result'} or response['state'] != 'response' or response['record_id'] != request['record_id']:
                raise RuntimeFailure('invalid_response')
            # Pure graph recomputation is part of the request deadline, not unbounded post-work.
            remaining = timeout - (time.monotonic() - request_started)
            if remaining <= 0:
                raise RuntimeFailure('deadline')
            def expired(*_args: object) -> None:
                raise RuntimeFailure('deadline')
            old_handler = signal.getsignal(signal.SIGALRM)
            if signal.getitimer(signal.ITIMER_REAL)[0] != 0:
                raise RuntimeFailure('deadline_signal_in_use')
            signal.signal(signal.SIGALRM, expired)
            signal.setitimer(signal.ITIMER_REAL, remaining)
            try:
                verify_result(request, response['result'], self.bundle_sha, self.code)
                if response['result']['provenance'] != self.ready['provenance']:
                    raise RuntimeFailure('provenance_changed')
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old_handler)
            self.state = 'ready'
            return response['result']
        except BaseException:
            self.state = 'failed'
            await self.close()
            raise
        finally:
            self.busy = False

    async def close(self) -> None:
        if self.cleanup_seconds is not None:
            return
        started = time.monotonic()
        shutdown_failed = False
        if self.proc is not None:
            if self.proc.returncode is None:
                try:
                    if self.state == 'ready' and not self.busy:
                        response = await self._exchange({'state': 'shutdown'}, 1)
                        if response != {'state': 'shutdown'}:
                            raise RuntimeFailure('invalid_shutdown')
                        await asyncio.wait_for(self.proc.wait(), 1)
                    else:
                        raise RuntimeFailure('forced_shutdown')
                except (Exception, asyncio.CancelledError):
                    shutdown_failed = self.state == 'ready' and not self.busy
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(self.proc.pid, signal.SIGKILL)
            try:
                await asyncio.wait_for(self.proc.wait(), 2)
            except asyncio.TimeoutError:
                raise RuntimeFailure('cleanup_failed') from None
            if self.proc.stdin is not None:
                self.proc.stdin.close()
        self.cleanup_seconds = time.monotonic() - started
        if self.cleanup_seconds > CLEANUP_SECONDS:
            raise RuntimeFailure('cleanup_failed')
        if self.state != 'failed':
            self.state = 'closed'
        if shutdown_failed:
            self.state = 'failed'
            raise RuntimeFailure('shutdown_failed')
