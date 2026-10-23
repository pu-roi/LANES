"""Resource evidence compatible with the separately approved cloud-run-v1 profile.

The original qualification probe and its frozen receipts remain unchanged.
Configured cloud limits are verified by the deployment controller separately.
"""
from pathlib import Path
import os

MEMORY_BYTES = 3 * 1024**3
HEADROOM_BYTES = 2688 * 1024**2


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


STRICT_PROFILE = 'local-strict-v1'
CLOUD_PROFILE = 'cloud-run-v1'
RESOURCE_PROFILES = (STRICT_PROFILE, CLOUD_PROFILE)
RESOURCE_FILES = {
    'v2_cpu': 'cpu.max', 'v2_memory_limit': 'memory.max',
    'v2_swap_limit': 'memory.swap.max', 'v2_memory_peak': 'memory.peak',
    'v1_cpu_quota': 'cpu/cpu.cfs_quota_us', 'v1_cpu_period': 'cpu/cpu.cfs_period_us',
    'v1_cpu_combined_quota': 'cpu,cpuacct/cpu.cfs_quota_us',
    'v1_cpu_combined_period': 'cpu,cpuacct/cpu.cfs_period_us',
    'v1_memory_limit': 'memory/memory.limit_in_bytes',
    'v1_memory_peak': 'memory/memory.max_usage_in_bytes',
    'v1_memory_and_swap_limit': 'memory/memory.memsw.limit_in_bytes',
    'v1_memory_and_swap_peak': 'memory/memory.memsw.max_usage_in_bytes',
}


def read_resource(root: Path, key: str) -> str:
    try:
        with (root / RESOURCE_FILES[key]).open(encoding='ascii') as stream:
            value = stream.read(129).strip()
        require(len(value) <= 128, 'resource_text_limit')
        return value
    except OSError as error:
        error.resource_key = key
        raise


def swap_inventory(proc: Path = Path('/proc')) -> dict:
    """Bounded host swap facts, never filenames or a substitute for a swap limit."""
    try:
        with (proc / 'swaps').open(encoding='ascii') as stream:
            text = stream.read(65537)
        require(len(text) <= 65536, 'swap_inventory_limit')
        lines = text.splitlines()
        require(bool(lines) and lines[0].split() == ['Filename', 'Type', 'Size', 'Used', 'Priority'],
                'swap_inventory_format')
        rows = [line.split() for line in lines[1:] if line.strip()]
        require(all(len(row) == 5 and row[2].isdigit() and row[3].isdigit() for row in rows),
                'swap_inventory_format')
        with (proc / 'meminfo').open(encoding='ascii') as stream:
            info = stream.read(65537)
        require(len(info) <= 65536, 'swap_inventory_limit')
        selected = {}
        for line in info.splitlines():
            parts = line.split()
            if parts and parts[0] in ('SwapTotal:', 'SwapFree:'):
                require(len(parts) == 3 and parts[1].isdigit() and parts[2] == 'kB'
                        and parts[0] not in selected, 'swap_inventory_format')
                selected[parts[0]] = int(parts[1]) * 1024
        require(set(selected) == {'SwapTotal:', 'SwapFree:'}, 'swap_inventory_incomplete')
        return {'status': 'readable', 'active_devices': len(rows),
                'total_bytes': selected['SwapTotal:'], 'free_bytes': selected['SwapFree:'],
                'host_reports_no_swap': not rows and selected['SwapTotal:'] == selected['SwapFree:'] == 0,
                'establishes_container_swap_limit': False}
    except (OSError, ValueError) as error:
        return {'status': 'unavailable', 'error_type': type(error).__name__,
                'establishes_container_swap_limit': False}


def resource_readings(root: Path = Path('/sys/fs/cgroup')) -> dict:
    """Read either controller layout; never fall back from invalid partial v2 data."""
    if (root / RESOURCE_FILES['v2_cpu']).exists():
        words = read_resource(root, 'v2_cpu').split()
        require(len(words) == 2 and all(word.isdecimal() for word in words), 'cpu_limit_required')
        quota, period = map(int, words)
        memory = int(read_resource(root, 'v2_memory_limit'))
        swap = int(read_resource(root, 'v2_swap_limit'))
        peak = int(read_resource(root, 'v2_memory_peak'))
        layout = 'v2'
        combined = None
    else:
        combined_cpu = (root / RESOURCE_FILES['v1_cpu_combined_quota']).exists()
        prefix = 'v1_cpu_combined_' if combined_cpu else 'v1_cpu_'
        quota = int(read_resource(root, prefix + 'quota'))
        period = int(read_resource(root, prefix + 'period'))
        memory = int(read_resource(root, 'v1_memory_limit'))
        combined = int(read_resource(root, 'v1_memory_and_swap_limit'))
        require(combined >= memory, 'memory_swap_limit_invalid')
        # Large kernel sentinel values mean effectively unbounded; do not invent
        # zero swap. Strings preserve these integers through Cloud Logging Struct.
        swap = combined - memory if combined < 2**60 else None
        peak = int(read_resource(root, 'v1_memory_peak'))
        layout = 'v1'
    require(period > 0 and peak >= 0 and memory > 0 and (swap is None or swap >= 0), 'resource_values_invalid')
    return {'layout': layout, 'cpu_quota': quota, 'cpu_period': period,
            'memory_max': memory, 'swap_max': swap, 'peak': peak,
            'memory_and_swap_limit_decimal': str(combined) if combined is not None else None}


def resource_snapshot(root: Path = Path('/sys/fs/cgroup'), *, profile: str = STRICT_PROFILE,
                      proc: Path = Path('/proc')) -> dict:
    require(profile in RESOURCE_PROFILES, 'resource_profile_invalid')
    value = resource_readings(root)
    value['profile'] = profile
    if profile == CLOUD_PROFILE:
        host = swap_inventory(proc)
        basis = 'enforced_zero_limit' if value['swap_max'] == 0 else 'host_no_swap'
        value['swap_evidence'] = {'basis': basis, 'host': host}
    return value


def validate_resources(value: dict, *, profile: str = STRICT_PROFILE) -> None:
    require(profile in RESOURCE_PROFILES, 'resource_profile_invalid')
    if profile == STRICT_PROFILE:
        require(value['cpu_quota'] == value['cpu_period'] > 0, 'cpu_limit_required')
        require(value['memory_max'] == MEMORY_BYTES and value['swap_max'] == 0, 'memory_limit_required')
    else:
        require(value['cpu_quota'] > 0 and value['cpu_period'] > 0, 'cpu_limit_required')
        require(value['memory_max'] == MEMORY_BYTES, 'memory_limit_required')
        evidence = value['swap_evidence']
        if evidence['basis'] == 'enforced_zero_limit':
            require(value['swap_max'] == 0, 'swap_evidence_required')
        else:
            host = evidence['host']
            require(evidence['basis'] == 'host_no_swap' and host.get('status') == 'readable'
                    and host.get('host_reports_no_swap') is True
                    and host.get('active_devices') == host.get('total_bytes') == host.get('free_bytes') == 0
                    and host.get('establishes_container_swap_limit') is False, 'swap_evidence_required')


def resources(root: Path = Path('/sys/fs/cgroup'), *, profile: str = STRICT_PROFILE,
              proc: Path = Path('/proc')) -> dict:
    value = resource_snapshot(root, profile=profile, proc=proc)
    validate_resources(value, profile=profile)
    return value



def checkpoint() -> dict:
    profile = os.environ.get('LANES_HISTORY_RESOURCE_PROFILE', STRICT_PROFILE)
    value = resources(profile=profile)
    require(value['peak'] < HEADROOM_BYTES, 'historical_memory_headroom_exceeded')
    return value
