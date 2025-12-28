from datetime import datetime
from zoneinfo import ZoneInfo


def tz_to_offset(tz_name: str, dt: datetime = None) -> str:
    """
    Convert a timezone name to a UTC offset string in ±HH:MM format.

    Args:
        tz_name (str): Timezone name, e.g., 'Europe/Kyiv'.
        dt (datetime, optional): Specific datetime to calculate the offset.
                                 Defaults to current time.

    Returns:
        str: UTC offset in the format '+HH:MM' or '-HH:MM'.

    Example:
        >>> tz_to_binance_offset("Europe/Kyiv")
        '+03:00'
    """
    if dt is None:
        dt = datetime.now()
    local_dt = dt.replace(tzinfo=ZoneInfo(tz_name))
    offset = local_dt.utcoffset()
    total_minutes = int(offset.total_seconds() // 60)
    hours = total_minutes // 60
    minutes = abs(total_minutes % 60)
    return f"{hours:+03d}:{minutes:02d}"
