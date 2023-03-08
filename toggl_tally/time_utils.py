from datetime import datetime, timezone
from typing import Union

from dateutil import tz


def get_current_datetime(local_timezone: Union[str, None] = None) -> str:
    local_tz = tz.gettz(local_timezone) if local_timezone is not None else None
    return datetime.now(timezone.utc).astimezone(local_tz)


def get_current_timestamp(local_timezone: Union[str, None] = None) -> str:
    """
    RFC3339 format https://developers.track.toggl.com/docs/api/time_entries

    >>> get_current_timestamp(local_timezone="Africa/Johannesburg")[-6:]
    '+02:00'
    """
    local_time = get_current_datetime(local_timezone)
    return local_time.isoformat()


def format_seconds(seconds: float) -> str:
    """
    >>> format_seconds(3600)
    '01:00:00'
    >>> format_seconds(3662)
    '01:01:02'
    """
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}"
