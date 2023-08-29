import functions_framework
import os
from datetime import datetime, timedelta
from cloudevents.http.event import CloudEvent
from esbdata.esb import fetchCSVData, User, READ_TYPE
from esbdata.bigquery import BigQuery

MPRN = os.getenv("ESB_MPRN")
USERNAME = os.getenv("ESB_USERNAME")
PASSWORD = os.getenv("ESB_PASSWORD")


@functions_framework.cloud_event
def loadToBigQuery(cloud_event: CloudEvent) -> None:
    user = User(mprn=MPRN, username=USERNAME, password=PASSWORD)
    data = fetchCSVData(user)
    bq = BigQuery()

    yesterday = datetime.today() - timedelta(days=1)
    startDate = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)
    endDate = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)
    
    allRows = []
    for logged, value in data.importData.items():
        if logged < startDate or logged > endDate:
            # If logged time is before startDate or after endDate
            continue

        allRows.append({
            'logged_at': logged.strftime('%Y-%m-%dT%H:%M:%S'),
            'read_type': READ_TYPE.IMPORT.value,
            'read_value': value,
        })

    for logged, value in data.exportData.items():
        if logged < startDate or logged > endDate:
            # If logged time is before startDate or after endDate
            continue
        allRows.append({
            'logged_at': logged.strftime('%Y-%m-%dT%H:%M:%S'),
            'read_type': READ_TYPE.EXPORT.value,
            'read_value': value,
        })
    
    bq.insert_rows(allRows)
