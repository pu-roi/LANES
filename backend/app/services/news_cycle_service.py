"""Bounded worker attempt diagnostics in existing runtime JSON; never article evidence."""
import os
import re
from datetime import datetime
from app.schemas.configuration import ConfigurationRuntime, NewsCycleSummary

STAGES = frozenset(('maintenance','collection','pipeline','extraction','seed','evaluation','publication','footprints'))


def safe_code(value: object) -> str:
    return value if isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,99}', value) else 'stage_failed'


def attempt_identity() -> dict:
    name = os.environ.get('CLOUD_RUN_EXECUTION', '')
    result = {'execution_name': name if re.fullmatch(r'[a-z][a-z0-9-]{0,127}', name) else None}
    for field, key in (('task_index','CLOUD_RUN_TASK_INDEX'),('task_attempt','CLOUD_RUN_TASK_ATTEMPT')):
        raw = os.environ.get(key, '')
        result[field] = int(raw) if re.fullmatch(r'[0-9]{1,9}', raw) else None
    return result


def finish_cycle(runtime: ConfigurationRuntime, now: datetime, identity: dict) -> NewsCycleSummary:
    cycle = NewsCycleSummary(started_at=runtime.last_started_at, finished_at=now,
        outcome='requires_attention' if runtime.error_code else 'completed',
        error_code=safe_code(runtime.error_code) if runtime.error_code else None,
        counts={stage: {key: value for key, value in counts.items()
            if re.fullmatch(r'[a-z][a-z0-9_]{0,63}', key) and isinstance(value,int) and not isinstance(value,bool)}
            for stage, counts in runtime.stage_counts.items() if stage in STAGES},
        stage_outcomes={stage: safe_code(runtime.stages[stage].outcome
            if stage in runtime.stages and runtime.stages[stage].last_attempt_at==runtime.last_started_at else value)
            for stage,value in runtime.stage_outcomes.items() if stage in STAGES},
        stage_errors={stage: sorted({safe_code(error) for error in health.errors})[:20]
            for stage,health in runtime.stages.items() if stage in STAGES and health.last_attempt_at==runtime.last_started_at},
        **identity)
    def key(value: NewsCycleSummary) -> tuple:
        return (value.started_at,value.execution_name,value.task_index,value.task_attempt)
    previous = list(runtime.recent_cycles)
    if runtime.last_cycle and all(key(row)!=key(runtime.last_cycle) for row in previous):
        previous.append(runtime.last_cycle)
    # Frozen completed attempts are never replaced by repeated finalization.
    existing = next((row for row in previous if key(row)==key(cycle)),None)
    if existing is not None:
        runtime.last_cycle=existing
        return existing
    runtime.last_cycle=cycle
    runtime.recent_cycles=sorted([cycle,*previous],key=lambda row:row.started_at,reverse=True)[:10]
    return cycle
