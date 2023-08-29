from datetime import datetime, timedelta, timezone

DATETIME_FORMAT_STR = "%d-%m-%Y %H:%M"


def parseDate(dateString: str) -> datetime:
    return datetime.strptime(dateString, DATETIME_FORMAT_STR)

def divide_chunks(list_to_chunk, chunk_size):
    # looping till length l
    for i in range(0, len(list_to_chunk), chunk_size):
        yield list_to_chunk[i:i + chunk_size]
