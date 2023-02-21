from datetime import datetime

import pytest


@pytest.mark.parametrize(
    "toggl_tally_object,expected_next_working_day",
    [
        pytest.param(
            dict(now=datetime(2023, 2, 17), skip_today=False),
            datetime(2023, 2, 17),
            id="next_working_day_friday",
        ),
        pytest.param(
            dict(now=datetime(2023, 2, 17), skip_today=True),
            datetime(2023, 2, 20),
            id="next_working_day_friday_skip_today",
        ),
        pytest.param(
            dict(now=datetime(2023, 2, 20), skip_today=False),
            datetime(2023, 2, 20),
            id="next_working_day_monday",
        ),
        pytest.param(
            dict(now=datetime(2023, 2, 20), skip_today=True),
            datetime(2023, 2, 21),
            id="next_working_day_monday_skip_today",
        ),
    ],
    indirect=["toggl_tally_object"],
)
def test_toggl_tally_next_working_day(toggl_tally_object, expected_next_working_day):
    assert toggl_tally_object.next_working_day == expected_next_working_day


@pytest.mark.parametrize(
    "toggl_tally_object,expected_last_invoice_date,expected_next_invoice_date",
    [
        pytest.param(
            dict(now=datetime(2023, 2, 17), invoice_day_of_month=15),
            datetime(2023, 2, 15),
            datetime(2023, 3, 15),
            id="invoice_date_current_month",
        ),
        pytest.param(
            dict(now=datetime(2023, 2, 17), invoice_day_of_month=29),
            datetime(2023, 1, 27),
            datetime(2023, 2, 28),
            id="invoice_date_last_month",
        ),
    ],
    indirect=["toggl_tally_object"],
)
def test_toggl_tally_invoice_dates(
    toggl_tally_object, expected_last_invoice_date, expected_next_invoice_date
):
    assert toggl_tally_object.last_invoice_date == expected_last_invoice_date
    assert toggl_tally_object.next_invoice_date == expected_next_invoice_date


@pytest.mark.parametrize(
    "toggl_tally_object,expected_last_billable_date",
    [
        pytest.param(
            dict(now=datetime(2023, 3, 1), invoice_day_of_month=31),
            datetime(2023, 3, 30),
            id="last_billable_date_exclusive",
        ),
        pytest.param(
            dict(now=datetime(2023, 3, 1), invoice_day_of_month=26),
            datetime(2023, 3, 24),
            id="last_billable_date_inclusive",
        ),
    ],
    indirect=["toggl_tally_object"],
)
def test_toggl_tally_last_billable_date(
    toggl_tally_object, expected_last_billable_date
):
    assert toggl_tally_object.last_billable_date == expected_last_billable_date


@pytest.mark.parametrize(
    "toggl_tally_object,expected_remaining_working_days",
    [
        pytest.param(
            dict(now=datetime(2023, 3, 1), invoice_day_of_month=31),
            22,
            id="remaining_working_days_case_1",
        ),
        pytest.param(
            dict(now=datetime(2023, 3, 1), invoice_day_of_month=31, skip_today=True),
            21,
            id="remaining_working_days_case_1_skip_today",
        ),
        pytest.param(
            dict(now=datetime(2023, 3, 1), invoice_day_of_month=26),
            18,
            id="remaining_working_days_case_2",
        ),
    ],
    indirect=["toggl_tally_object"],
)
def test_toggl_tally_remaining_working_days(
    toggl_tally_object, expected_remaining_working_days
):
    assert toggl_tally_object.remaining_working_days == expected_remaining_working_days
