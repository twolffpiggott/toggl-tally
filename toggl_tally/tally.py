from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from typing import List, Tuple, Union

import holidays
from dateutil import rrule

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
        country: str,
        skip_today: bool = False,
        timezone: Union[str, None] = None,
        working_days: List[str] = ["MO", "TU", "WE", "TH", "FR"],
        exclude_public_holidays: bool = True,
    ):
        self.invoice_day_of_month = invoice_day_of_month
        self.skip_today = skip_today
        self.timezone = timezone
        self.working_days = _get_rrule_days(working_days)
        self._working_day_ints = [DAY_OF_WEEK[day_str] for day_str in working_days]
        self.public_holidays = holidays.country_holidays(country, years=self.now.year)
        self.exclude_public_holidays = exclude_public_holidays

    @property
    def now(self) -> datetime:
        return get_current_datetime(self.timezone)

    @property
    def next_working_day(self) -> datetime:
        now = self.now
        next_working_day = datetime(
            day=now.day, month=now.month, year=now.year, tzinfo=now.tzinfo
        )
        if self.skip_today:
            next_working_day += timedelta(days=1)
        return self.get_next_workday_inclusive(next_working_day)

    @property
    def current_month_invoice_date(self) -> datetime:
        return self.calculate_invoice_date(
            self.invoice_day_of_month,
            self.now.month,
            self.now.year,
            tzinfo=self.now.tzinfo,
        )

    @property
    def last_invoice_date(self) -> datetime:
        if self.now < self.current_month_invoice_date:
            return self.calculate_invoice_date(
                self.invoice_day_of_month,
                self.now.month - 1,
                self.now.year,
                tzinfo=self.now.tzinfo,
            )
        else:
            return self.current_month_invoice_date

    @property
    def first_billable_date(self) -> datetime:
        last_invoice_date = self.last_invoice_date
        if last_invoice_date.day < self.invoice_day_of_month:
            # Return the next day
            return last_invoice_date + timedelta(days=1)
        else:
            # Return the last invoice date
            return last_invoice_date

    @property
    def next_invoice_date(self) -> datetime:
        if self.now < self.current_month_invoice_date:
            return self.current_month_invoice_date
        else:
            return self.calculate_invoice_date(
                self.invoice_day_of_month,
                self.now.month + 1,
                self.now.year,
                tzinfo=self.now.tzinfo,
            )

    @property
    def last_billable_date(self) -> datetime:
        # should be inclusive if the next invoice date is before the strict invoice date
        # i.e. you likely want to bill including this day
        if self.next_invoice_date.day < self.invoice_day_of_month:
            return self.next_invoice_date
        return self.get_last_workday_inclusive(
            self.next_invoice_date - timedelta(days=1)
        )

    @property
    def _remaining_working_days(self) -> List[datetime]:
        return list(
            rrule.rrule(
                freq=rrule.DAILY,
                dtstart=self.next_working_day,
                until=self.last_billable_date,
                byweekday=self.working_days,
            )
        )

    @property
    def remaining_working_days(self) -> int:
        working_days = self._remaining_working_days
        if self.exclude_public_holidays:
            return len([day for day in working_days if day not in self.public_holidays])
        return len(working_days)

    @property
    def remaining_public_holidays(self) -> List[Tuple[str, date]]:
        working_dates = [day.date() for day in self._remaining_working_days]
        holiday_tuples = []
        for holiday_date, holiday_name in self.public_holidays.items():
            if holiday_date in working_dates:
                holiday_tuples.append((holiday_name, holiday_date))
        return holiday_tuples

    def get_last_weekday_inclusive(self, date: datetime) -> datetime:
        shifted_date = date
        if self.exclude_public_holidays:
            while shifted_date.weekday() > 4 or shifted_date in self.public_holidays:
                shifted_date -= timedelta(days=1)
        else:
            while shifted_date.weekday() > 4:
                shifted_date -= timedelta(days=1)
        return shifted_date

    def get_last_workday_inclusive(self, date: datetime) -> datetime:
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

    def get_next_workday_inclusive(self, date: datetime) -> datetime:
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

    def calculate_invoice_date(
        self,
        invoice_day_of_month: int,
        month: int,
        year: int,
        tzinfo: Union[timezone, None],
    ) -> datetime:
        try:
            invoice_date = datetime(
                day=invoice_day_of_month, month=month, year=year, tzinfo=tzinfo
            )
        except ValueError:
            # assume the invoice day falls after the last day of the month
            last_day_of_month = monthrange(year, month)[1]
            invoice_date = datetime(
                day=last_day_of_month, month=month, year=year, tzinfo=tzinfo
            )
        # return invoice date or last week day before invoice date
        return self.get_last_weekday_inclusive(invoice_date)


def _get_rrule_days(day_strings: List[str]):
    rrule_days = []
    if not day_strings:
        raise ValueError("Working days should be non-empty")
    for day_str in day_strings:
        try:
            rrule_day = getattr(rrule, day_str)
        except AttributeError:
            raise ValueError(
                'Working days should use the codes: ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]'
            )
        rrule_days.append(rrule_day)
    return rrule_days
