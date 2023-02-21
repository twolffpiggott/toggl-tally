from calendar import monthrange
from datetime import datetime, timedelta
from typing import List, Union

from dateutil import rrule, tz

from toggl_tally.time_utils import get_current_datetime


class TogglTally(object):
    """
    Responsible for:
    - Calculating the last and next invoice dates
    - Calculating the remaining working days for the current invoice
    TODO check that invoice dates don't fall on public holidays
    """

    def __init__(
        self,
        invoice_day_of_month: int,
        skip_today: bool = False,
        timezone: Union[str, None] = None,
        working_days: List[str] = ["MO", "TU", "WE", "TH", "FR"],
    ):
        self.invoice_day_of_month = invoice_day_of_month
        self.skip_today = skip_today
        self.timezone = tz.gettz(timezone) if timezone is not None else None
        self.working_days = [getattr(rrule, day_str) for day_str in working_days]

    @property
    def now(self):
        return get_current_datetime(self.timezone)

    @property
    def next_working_day(self):
        if self.skip_today:
            next_working_day = self.now + timedelta(days=1)
            while next_working_day.weekday() > 4:  # Mon-Fri are 0-4
                next_working_day += timedelta(days=1)
            return next_working_day
        else:
            return self.now

    @property
    def current_month_invoice_date(self):
        return calculate_invoice_date(
            self.invoice_day_of_month, self.now.month, self.now.year
        )

    @property
    def last_invoice_date(self):
        if self.now < self.current_month_invoice_date:
            return calculate_invoice_date(
                self.invoice_day_of_month, self.now.month - 1, self.now.year
            )
        else:
            return self.current_month_invoice_date

    @property
    def next_invoice_date(self):
        if self.now < self.current_month_invoice_date:
            return self.current_month_invoice_date
        else:
            return calculate_invoice_date(
                self.invoice_day_of_month, self.now.month + 1, self.now.year
            )

    @property
    def last_billable_date(self):
        # should be inclusive if the next invoice date is before the strict invoice date
        # i.e. you likely want to bill including this day
        if self.next_invoice_date.day < self.invoice_day_of_month:
            return self.next_invoice_date
        return self.next_invoice_date - timedelta(days=1)

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
        return len(days)

    @property
    def get_current_date(self):
        pass


def calculate_invoice_date(invoice_day_of_month: int, month: int, year: int):
    try:
        invoice_date = datetime(day=invoice_day_of_month, month=month, year=year)
    except ValueError:
        # assume the invoice day falls after the last day of the month
        last_day_of_month = monthrange(year, month)[1]
        invoice_date = datetime(day=last_day_of_month, month=month, year=year)
    # find last week day before invoice date
    while invoice_date.weekday() > 4:  # Mon-Fri are 0-4
        invoice_date -= timedelta(days=1)
    return invoice_date
