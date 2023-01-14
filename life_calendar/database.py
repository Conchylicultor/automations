""".

"""

from __future__ import annotations

import dataclasses
import datetime

import auto_notion

CALENDAR_ID = "a70ad02a9ba1460089a7168fbfe2bd33"
YEAR_ZERO = 1992


class LifeCalendarDb:
    def __init__(self) -> None:
        self.db = auto_notion.Database(CALENDAR_ID)
        # Load all events, sorted per start date
        events = [LifeEvent.from_row(row) for row in self.db.pages]
        # events = [e for e in events if e.start]  # Filter event without start
        # events = sorted(events, key=lambda e: e.start)
        self.events = events


@dataclasses.dataclass
class Week:
    year: int
    week: int
    desc: str
    type: str
    event: LifeEvent = dataclasses.field(repr=False)
    date_range: str = dataclasses.field(init=False)
    country: str = None
    continent: str = None

    def __post_init__(self):
        start = self.event.start.strftime("%Y-%m-%d")
        if self.event.end is None:
            end = ""
        else:
            end = self.event.end.strftime("%Y-%m-%d")
        self.date_range = f"{start} - {end}"


@dataclasses.dataclass
class LifeEvent:
    desc: str
    start: datetime.datetime
    end: datetime.datetime | None
    lieu: None = None

    @classmethod
    def from_row(cls, row: auto_notion.Page):
        return cls(
            desc=row["Name"],
            start=row["Start"],
            end=row["End"],
        )

    def to_weeks(self) -> list[Week]:
        if self.start is None:
            print(f"Skipping: {self.desc}")
            return []

        # Compute the position of the first week
        # TODO: Make sure that it's possible to get to 52
        start_year_date = datetime.datetime(year=self.start.year, month=1, day=1)
        start_year = self.start.year - YEAR_ZERO  # Years start at 0
        start_week = (self.start - start_year_date).days // 7

        # Compute the number of week to add
        end = self.start if self.end is None else self.end
        num_weeks = _days2weeks((end - self.start).days)

        weeks = []
        for week_id in range(num_weeks):
            curr_week = (start_week + week_id) % 52
            curr_year = start_year + (start_week + week_id) // 52

            week = Week(
                year=curr_year,
                week=curr_week,
                desc=self.desc,
                type="",
                event=self,
            )
            weeks.append(week)
        return weeks


def _days2weeks(days: int) -> int:
    return max(days // 7, 1)  # If num_weeks ==0, set it to 1
