"""Read-only desktop hardware inventory; never installs, trains, or admits data.

Runnable directly with Python's standard library, before research dependencies
are installed on the desktop. A matching GPU is not CUDA qualification.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone


QUERY = ['--query-gpu=name,driver_version,memory.total,memory.free',
         '--format=csv,noheader,nounits']


def parse_gpus(text: str) -> list[dict]:
    """Reject incomplete driver output instead of reporting a usable desktop."""
    if not text.strip() or len(text) > 65536:
        raise ValueError('empty or excessive NVIDIA query output')
    rows = []
    for fields in csv.reader(io.StringIO(text), skipinitialspace=True):
        if not fields:
            continue
        if len(fields) != 4:
            raise ValueError('NVIDIA query must return four fields per GPU')
        name, driver, total, free = [field.strip() for field in fields]
        if (not name or not re.fullmatch(r'\d+(?:\.\d+)+', driver)
                or not total.isascii() or not total.isdecimal()
                or not free.isascii() or not free.isdecimal()
                or not 0 <= int(free) <= int(total) or int(total) <= 0):
            raise ValueError('unavailable or malformed NVIDIA name/driver/memory')
        target = re.fullmatch(r'(?:NVIDIA\s+)?(?:GeForce\s+)?RTX\s+3060\s+Ti', name, re.I) is not None
        rows.append({'name': name, 'driver_version': driver,
                     'memory_total_mib': int(total), 'memory_free_mib': int(free),
                     'matches_reported_target': target and int(total) >= 7680})
    if not rows:
        raise ValueError('no NVIDIA devices returned')
    return rows


def physical_memory_bytes() -> int | None:
    """Best-effort system RAM inventory, with unknown kept explicit."""
    if os.name == 'nt':
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong),
                        ('total_physical', ctypes.c_ulonglong), ('available_physical', ctypes.c_ulonglong),
                        ('total_page', ctypes.c_ulonglong), ('available_page', ctypes.c_ulonglong),
                        ('total_virtual', ctypes.c_ulonglong), ('available_virtual', ctypes.c_ulonglong),
                        ('available_extended', ctypes.c_ulonglong)]

        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return status.total_physical
        return None
    try:
        value = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
        return value if value > 0 else None
    except (OSError, ValueError, AttributeError):
        return None


def collect_inventory() -> dict:
    """Query the local driver, without touching CUDA, models, or news captures."""
    result = {'schema_version': 'lanes-desktop-inventory-v1',
              'captured_at': datetime.now(timezone.utc).isoformat(),
              'system': {'os': platform.system(), 'release': platform.release(),
                         'architecture': platform.machine(), 'processor': platform.processor(),
                         'logical_cpus': os.cpu_count(), 'physical_memory_bytes': physical_memory_bytes()},
              'runner_python': {'version': platform.python_version(), 'executable': sys.executable,
                                'is_research_environment_qualification': False},
              'gpus': [], 'errors': [], 'state': 'inventory_failed',
              'gpu_training_qualified': False, 'source_admission_changed': False,
              'packages_installed': False, 'model_loaded': False, 'news_processed': False,
              'remaining_checks': ['Finalize the supported source-use decision before news-model processing.',
                                   'Resolve and hash-lock an isolated CPython 3.11/spaCy 3.7.5 GPU environment.',
                                   'Verify CuPy/spaCy GPU selection and the pinned model with constructed inputs.',
                                   'Measure a constructed training step, CUDA memory and CPU replay before news training.']}
    executable = shutil.which('nvidia-smi')
    if executable is None:
        result['errors'].append('nvidia-smi not found; NVIDIA driver/GPU availability is unknown')
        return result
    result['query'] = {'executable': executable, 'arguments': QUERY}
    try:
        response = subprocess.run([executable, *QUERY], capture_output=True, text=True,
                                  encoding='utf-8', errors='replace', timeout=15, check=True)
        result['query']['stdout'] = response.stdout[:65536]
        result['query']['stderr'] = response.stderr[:4096]
        result['gpus'] = parse_gpus(response.stdout)
        result['state'] = ('target_inventory_ready' if any(g['matches_reported_target'] for g in result['gpus'])
                           else 'awaiting_target_desktop')
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        result['errors'].append(f'{type(exc).__name__}: {str(exc)[:4096]}')
        if isinstance(exc, subprocess.CalledProcessError):
            result['query'].update({'returncode': exc.returncode,
                                    'stdout': str(exc.stdout or '')[:65536],
                                    'stderr': str(exc.stderr or '')[:4096]})
    return result


def save_inventory(output: Path, root: Path) -> dict:
    """Write only a fresh ignored report, preserving every earlier checkpoint."""
    artifacts = (root / 'backend/training/flood_ner/artifacts').resolve()
    destination = output.resolve()
    if not destination.is_relative_to(artifacts) or destination == artifacts or destination.exists():
        raise ValueError('inventory output must be a new directory under ignored artifacts')
    result = collect_inventory()
    parent = destination.parent
    while not parent.exists():
        parent = parent.parent
    result['system']['output_volume_free_bytes'] = shutil.disk_usage(parent).free
    result['collector_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    destination.mkdir(parents=True, exist_ok=False)
    encoded = (json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
    (destination / 'inventory.json').write_bytes(encoded)
    manifest = {'schema_version': 'lanes-desktop-inventory-manifest-v1',
                'gpu_training_qualified': False,
                'files': {'inventory.json': hashlib.sha256(encoded).hexdigest()}}
    (destination / 'manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = save_inventory(args.output, Path(__file__).resolve().parents[3])
    except (OSError, ValueError) as exc:
        print(f'desktop inventory failed: {exc}', file=sys.stderr)
        return 1
    print(json.dumps({'state': result['state'], 'gpu_training_qualified': False,
                      'errors': result['errors'], 'output': str(args.output)}, ensure_ascii=True))
    return 0 if result['state'] == 'target_inventory_ready' else 2


if __name__ == '__main__':
    raise SystemExit(main())
