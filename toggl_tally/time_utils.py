from datetime import datetime, timezone
from typing import Union

from dateutil import tz


def get_current_timestamp(local_timezone: Union[str, None] = None) -> str:
    """
    RFC3339 format https://developers.track.toggl.com/docs/api/time_entries

    >>> get_current_timestamp(local_timezone="SAST")[-6:]
    '+02:00'
    """
    local_tz = tz.gettz(local_timezone) if local_timezone is not None else None
    local_time = datetime.now(timezone.utc).astimezone(local_tz)
    return local_time.isoformat()
