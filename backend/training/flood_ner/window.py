"""Explicit inclusive publication dates; date evidence is not an observation clock."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PublicationWindow:
    start: date = date(2022, 1, 1)
    end: date = date(2026, 10, 14)

    def __post_init__(self) -> None:
        if type(self.start) is not date or type(self.end) is not date or self.start > self.end:
            raise ValueError('publication window requires ordered calendar dates')

    def contains(self, day: date | None) -> bool:
        return day is not None and self.start <= day <= self.end

    def as_list(self) -> list[str]:
        return [self.start.isoformat(), self.end.isoformat()]

    @classmethod
    def parse(cls, values: list[str]) -> 'PublicationWindow':
        if not isinstance(values, list) or len(values) != 2:
            raise ValueError('publication window needs exactly two ISO calendar dates')
        try:
            return cls(*(date.fromisoformat(v) for v in values))
        except (TypeError, ValueError) as exc:
            raise ValueError('invalid publication window') from exc


LEGACY_WINDOW = PublicationWindow()
REVISION_WINDOW = PublicationWindow(date(2017, 1, 1), date(2026, 10, 14))
