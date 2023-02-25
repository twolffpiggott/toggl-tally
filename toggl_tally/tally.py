from calendar import monthrange
from datetime import datetime, timedelta
from typing import List, Union

import holidays
from dateutil import rrule, tz

from toggl_tally.time_utils import get_current_datetime

DAY_OF_WEEK = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}


class TogglTally(object):
    """
    Responsible for:
    - Calculating the last and next invoice dates
    - Calculating the remaining working days for the current invoice
    - Optionally excluding public holidays from invoiceable dates
    """

    def __init__(
        self,
        invoice_day_of_month: int,
        skip_today: bool = False,
        timezone: Union[str, None] = None,
        working_days: List[str] = ["MO", "TU", "WE", "TH", "FR"],
        country_str: str = "ZA",
        exclude_public_holidays: bool = True,
    ):
        self.invoice_day_of_month = invoice_day_of_month
        self.skip_today = skip_today
        self.timezone = tz.gettz(timezone) if timezone is not None else None
        self.working_days = _get_rrule_days(working_days)
        self._working_day_ints = [DAY_OF_WEEK[day_str] for day_str in working_days]
        self.public_holidays = holidays.country_holidays(
            country_str, years=self.now.year
        )
        self.exclude_public_holidays = exclude_public_holidays

    @property
    def now(self):
        return get_current_datetime(self.timezone)

    @property
    def next_working_day(self):
        next_working_day = self.now
        if self.skip_today:
            next_working_day += timedelta(days=1)
        return self.get_next_workday_inclusive(next_working_day)

    @property
    def current_month_invoice_date(self):
        return self.calculate_invoice_date(
            self.invoice_day_of_month, self.now.month, self.now.year
        )

    @property
    def last_invoice_date(self):
        if self.now < self.current_month_invoice_date:
            return self.calculate_invoice_date(
                self.invoice_day_of_month, self.now.month - 1, self.now.year
            )
        else:
            return self.current_month_invoice_date

    @property
    def next_invoice_date(self):
        if self.now < self.current_month_invoice_date:
            return self.current_month_invoice_date
        else:
            return self.calculate_invoice_date(
                self.invoice_day_of_month, self.now.month + 1, self.now.year
            )

    @property
    def last_billable_date(self):
        # should be inclusive if the next invoice date is before the strict invoice date
        # i.e. you likely want to bill including this day
        if self.next_invoice_date.day < self.invoice_day_of_month:
            return self.next_invoice_date
        return self.get_last_workday_inclusive(
            self.next_invoice_date - timedelta(days=1)
        )

    @property
    def remaining_working_days(self):
        days = list(
            rrule.rrule(
                freq=rrule.DAILY,
                dtstart=self.next_working_day,
                until=self.last_billable_date,
                byweekday=self.working_days,
            )
        )
        if self.exclude_public_holidays:
            return len([day for day in days if day not in self.public_holidays])
        return len(days)

    def get_last_weekday_inclusive(self, date: datetime):
        shifted_date = date
        if self.exclude_public_holidays:
            while shifted_date.weekday() > 4 or shifted_date in self.public_holidays:
                shifted_date -= timedelta(days=1)
        else:
            while shifted_date.weekday() > 4:
                shifted_date -= timedelta(days=1)
        return shifted_date

    def get_last_workday_inclusive(self, date: datetime):
        shifted_date = date
        if self.exclude_public_holidays:
            while (
                shifted_date.weekday() not in self._working_day_ints
                or shifted_date in self.public_holidays
            ):
                shifted_date -= timedelta(days=1)
        else:
            while shifted_date.weekday() not in self._working_day_ints:
                shifted_date -= timedelta(days=1)
        return shifted_date

    def get_next_workday_inclusive(self, date: datetime):
        shifted_date = date
        if self.exclude_public_holidays:
            while (
                shifted_date.weekday() not in self._working_day_ints
                or shifted_date in self.public_holidays
            ):
                shifted_date += timedelta(days=1)
        else:
            while shifted_date.weekday() not in self._working_day_ints:
                shifted_date += timedelta(days=1)
        return shifted_date

    def calculate_invoice_date(self, invoice_day_of_month: int, month: int, year: int):
        try:
            invoice_date = datetime(day=invoice_day_of_month, month=month, year=year)
        except ValueError:
            # assume the invoice day falls after the last day of the month
            last_day_of_month = monthrange(year, month)[1]
            invoice_date = datetime(day=last_day_of_month, month=month, year=year)
        # return invoice date or last week day before invoice date
        return self.get_last_weekday_inclusive(invoice_date)


def _get_rrule_days(day_strings: List[str]):
    rrule_days = []
    for day_str in day_strings:
        try:
            rrule_day = getattr(rrule, day_str)
        except AttributeError:
            raise ValueError(
                'Working days should use the codes: ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]'
            )
        rrule_days.append(rrule_day)
    return rrule_days
