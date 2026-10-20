"""Linux amd64 seccomp network denial and parent-death containment."""
from __future__ import annotations

import ctypes
import errno
import os
import platform
import signal
import socket


def install() -> dict:
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise RuntimeError('isolation_unsupported')
    libc = ctypes.CDLL(None, use_errno=True)
    parent = os.getppid()
    if parent == 1 or libc.prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent:
        raise RuntimeError('parent_guard_failed')

    class Instruction(ctypes.Structure):
        _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte), ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint)]
    class Program(ctypes.Structure):
        _fields_ = [('len', ctypes.c_ushort), ('filter', ctypes.POINTER(Instruction))]
    # Reject wrong architectures and x32 ABI; no inherited socket descriptors exist.
    instructions = [(0x20, 0, 0, 4), (0x15, 1, 0, 0xC000003E), (0x06, 0, 0, 0x80000000),
                    (0x20, 0, 0, 0), (0x45, 0, 1, 0x40000000), (0x06, 0, 0, 0x00050000 | errno.EPERM)]
    # socket through socketpair; send/receive message variants; io_uring cannot bypass denial.
    for syscall in [*range(41, 56), 288, 299, 307, 425, 426, 427]:
        instructions.extend([(0x15, 0, 1, syscall), (0x06, 0, 0, 0x00050000 | errno.EPERM)])
    instructions.append((0x06, 0, 0, 0x7FFF0000))
    code = (Instruction * len(instructions))(*(Instruction(*i) for i in instructions))
    program = Program(len(instructions), code)
    if libc.prctl(38, 1, 0, 0, 0) != 0 or libc.prctl(22, 2, ctypes.byref(program), 0, 0) != 0:
        raise RuntimeError('seccomp_failed')
    checked = []
    for family in (socket.AF_INET, socket.AF_INET6, socket.AF_UNIX):
        try:
            sock = socket.socket(family, socket.SOCK_STREAM)
        except OSError as exc:
            if exc.errno != errno.EPERM:
                raise RuntimeError('socket_denial_failed') from None
            checked.append(int(family))
        else:
            sock.close()
            raise RuntimeError('socket_denial_failed')
    # Raw syscall proves this is not a Python socket monkeypatch.
    if libc.syscall(41, socket.AF_INET, socket.SOCK_STREAM, 0) != -1 or ctypes.get_errno() != errno.EPERM:
        raise RuntimeError('raw_socket_denial_failed')
    return {'seccomp': True, 'socket_families_denied': checked, 'raw_socket_denied': True, 'parent_death_signal': True}
