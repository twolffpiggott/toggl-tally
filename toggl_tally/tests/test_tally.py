import re
from datetime import date, datetime

import pytest
from dateutil import rrule

import toggl_tally.tally as sut


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
        pytest.param(
            dict(now=datetime(2023, 2, 25), skip_today=False),
            datetime(2023, 2, 27),
            id="next_working_day_saturday",
        ),
        pytest.param(
            dict(now=datetime(2023, 2, 25), skip_today=True),
            datetime(2023, 2, 27),
            id="next_working_day_saturday_skip_today",
        ),
        pytest.param(
            dict(now=datetime(2023, 4, 7), skip_today=True),
            datetime(2023, 4, 11),
            id="next_working_day_za_public_holiday",
        ),
        pytest.param(
            dict(now=datetime(2023, 4, 6), skip_today=True),
            datetime(2023, 4, 11),
            id="next_working_day_za_public_holiday_skip_today",
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
        pytest.param(
            dict(now=datetime(2023, 3, 17), invoice_day_of_month=21),
            datetime(2023, 2, 21),
            datetime(2023, 3, 20),
            id="invoice_date_current_month_public_holiday",
        ),
        pytest.param(
            dict(now=datetime(2023, 6, 17), invoice_day_of_month=20),
            datetime(2023, 5, 19),
            datetime(2023, 6, 20),
            id="invoice_date_weekend",
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
        pytest.param(
            dict(now=datetime(2023, 5, 17), invoice_day_of_month=20),
            datetime(2023, 5, 19),
            id="last_billable_date_inclusive_2",
        ),
        pytest.param(
            dict(now=datetime(2023, 3, 1), invoice_day_of_month=21),
            datetime(2023, 3, 20),
            id="last_billable_date_inclusive_public_holiday",
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
            dict(
                now=datetime(2023, 3, 1),
                invoice_day_of_month=31,
                exclude_public_holidays=False,
            ),
            22,
            id="remaining_working_days_case_1",
        ),
        pytest.param(
            dict(
                now=datetime(2023, 3, 1),
                invoice_day_of_month=31,
                skip_today=True,
                exclude_public_holidays=False,
            ),
            21,
            id="remaining_working_days_case_1_skip_today",
        ),
        pytest.param(
            dict(
                now=datetime(2023, 3, 1),
                invoice_day_of_month=26,
                exclude_public_holidays=False,
            ),
            18,
            id="remaining_working_days_case_2",
        ),
        pytest.param(
            dict(
                now=datetime(2023, 3, 1),
                invoice_day_of_month=26,
                exclude_public_holidays=True,
            ),
            17,
            id="remaining_working_days_case_2_public_holiday",
        ),
        pytest.param(
            dict(
                now=datetime(2023, 3, 1, 14, 45, 40),
                invoice_day_of_month=26,
                exclude_public_holidays=False,
            ),
            18,
            id="remaining_working_days_case_2_time_info",
        ),
    ],
    indirect=["toggl_tally_object"],
)
def test_toggl_tally_remaining_working_days(
    toggl_tally_object, expected_remaining_working_days
):
    assert toggl_tally_object.remaining_working_days == expected_remaining_working_days


@pytest.mark.parametrize(
    "toggl_tally_object,expected_remaining_public_holidays",
    [
        pytest.param(
            dict(
                now=datetime(2023, 3, 1),
                invoice_day_of_month=31,
                exclude_public_holidays=True,
            ),
            [("Human Rights Day", date(2023, 3, 21))],
            id="remaining_public_holidays",
        )
    ],
    indirect=["toggl_tally_object"],
)
def test_toggl_tally_remaining_public_holidays(
    toggl_tally_object, expected_remaining_public_holidays
):
    assert (
        toggl_tally_object.remaining_public_holidays
        == expected_remaining_public_holidays
    )


def test_toggle_tally_rrule_day_strs():
    expected_result = [
        rrule.MO,
        rrule.TU,
        rrule.WE,
        rrule.TH,
        rrule.FR,
        rrule.SA,
        rrule.SU,
    ]
    sut._get_rrule_days(["MO", "TU", "WE", "TH", "FR", "SA", "SU"]) == expected_result


def test_toggle_tally_rrule_day_strs_fails_for_invalid():
    exception_match_str = re.escape(
        'Working days should use the codes: ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]'
    )
    with pytest.raises(ValueError, match=exception_match_str):
        sut._get_rrule_days(["MO", "FO"])


def test_toggle_tally_rrule_day_strs_fails_for_empty():
    exception_match_str = re.escape("Working days should be non-empty")
    with pytest.raises(ValueError, match=exception_match_str):
        sut._get_rrule_days([])


@pytest.mark.parametrize(
    "toggl_tally_object,expected_first_billable_date",
    [
        pytest.param(
            dict(now=datetime(2023, 6, 18), invoice_day_of_month=19),
            datetime(2023, 5, 19),
            id="first_billable_date_inclusive",
        ),
        pytest.param(
            dict(now=datetime(2023, 6, 19), invoice_day_of_month=20),
            datetime(2023, 5, 20),
            id="first_billable_date_exclusive",
        ),
    ],
    indirect=["toggl_tally_object"],
)
def test_toggl_tally_first_billable_date(
    toggl_tally_object, expected_first_billable_date
):
    assert toggl_tally_object.first_billable_date == expected_first_billable_date
