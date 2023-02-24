from unittest.mock import PropertyMock, patch

import pytest

from toggl_tally.tally import TogglTally


@pytest.fixture()
def toggl_tally_object(request):
    kwargs = request.param
    with patch(
        "toggl_tally.tally.TogglTally.now", new_callable=PropertyMock
    ) as mock_toggl_tally_now:
        mock_toggl_tally_now.return_value = kwargs["now"]
        tally_object = TogglTally(
            invoice_day_of_month=kwargs.get("invoice_day_of_month", 1),
            skip_today=kwargs.get("skip_today", False),
            exclude_public_holidays=kwargs.get("exclude_public_holidays", True),
        )
        yield tally_object
