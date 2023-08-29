from datetime import datetime, timedelta, timezone

DATETIME_FORMAT_STR = "%Y-%m-%dT%H:%M:%S"


def parseDate(dateString: str) -> datetime:
    if len(dateString) == 19:
        return datetime.strptime(dateString, DATETIME_FORMAT_STR)
    else:
        # Separate datetime and timezone info
        dt = datetime.strptime(dateString[:19], DATETIME_FORMAT_STR)
        tz_offset = int(dateString[-6:-3])
        tz = timezone(timedelta(hours=tz_offset))
        return dt.replace(tzinfo=tz)
