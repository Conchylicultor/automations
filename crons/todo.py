"""Update the todo database."""

import dataclasses
import datetime
import os
import pathlib
import sys
from typing import Any

# Add notion to system path
root_dir = pathlib.Path(__file__).parent.parent
assert (root_dir / "auto_notion" / "__init__.py").exists()
sys.path.append(os.fspath(root_dir))


import auto_notion

# Shift TODAY from 7 hours (as 2am on Friday is still Thursday)
TODAY_DATE = datetime.datetime.today() - datetime.timedelta(hours=6)


def next_weekday(curr_day: datetime.datetime, day_id: int):
    day_ahead = (day_id - curr_day.weekday()) % 7
    if day_ahead == 0:
        day_ahead += 7
    return curr_day + datetime.timedelta(days=day_ahead)


def next_monthday(curr_day: datetime.datetime, month_id: int):
    if month_id > curr_day.month:  # Keep current year
        year = curr_day.year
    else:  # Month id already passed. Use next year
        year = curr_day.year + 1
    return datetime.datetime(year=year, month=month_id, day=1)


@dataclasses.dataclass
class NextWeek:
    day_id: int

    def __call__(self) -> Any:
        return next_weekday(TODAY_DATE, self.day_id)


@dataclasses.dataclass
class DetlaTime:
    days: int

    def __call__(self) -> Any:
        return TODAY_DATE + datetime.timedelta(days=self.days)


@dataclasses.dataclass
class InMonth:
    month_id: int

    def __call__(self) -> Any:
        return next_monthday(TODAY_DATE, self.month_id)


OPTION_TO_DELTA = {
    "Next Monday": NextWeek(0),
    "Next Tuesday": NextWeek(1),
    "Next Wednesday": NextWeek(2),
    "Next Thursday": NextWeek(3),
    "Next Friday": NextWeek(4),
    "Next Saturday": NextWeek(5),
    "Next Sunday": NextWeek(6),
    "In 1 Day": DetlaTime(1),
    "In 7 Days": DetlaTime(7),
    "In 1 Month": DetlaTime(30),
    "In 2 Months": DetlaTime(60),
    "In 1 Year": DetlaTime(365),
    "In Jan": InMonth(1),
    "In Feb": InMonth(2),
    "In Mar": InMonth(3),
    "In Apr": InMonth(4),
    "In May": InMonth(5),
    "In Jun": InMonth(6),
    "In Jul": InMonth(7),
    "In Aug": InMonth(8),
    "In Sep": InMonth(9),
    "In Oct": InMonth(10),
    "In Nov": InMonth(11),
    "In Dec": InMonth(12),
    "In the US": None,
}


def main():
    TODAY_DATE = datetime.datetime.today()

    db = auto_notion.Database("989b65ec51244c8ba318a982717b085d")

    print("Processing rows...")

    # TODO(epot): Should filter done & archived
    for row in db:
        if row.done:
            if not row.archived:
                row.archived = TODAY_DATE
        else:
            if not row.snooze:
                continue
            if row.snooze not in OPTION_TO_DELTA:
                raise ValueError(f"Unexpected snooze value: {row.snooze!r}")

            delta_fn = OPTION_TO_DELTA[row.snooze]
            if delta_fn is None:
                continue

            reminder = delta_fn().date()
            print(f"{row.snooze} -> {reminder}")
            row.reminder = reminder
            row.snooze = None
    print("Processing done!")


if __name__ == "__main__":
    main()
