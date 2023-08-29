import functions_framework
import os
from cloudevents.http.event import CloudEvent
from datetime import datetime, timedelta
from esb import fetchCSVData, User

MPRN = os.getenv("ESB_MPRN")
USERNAME = os.getenv("ESB_USERNAME")
PASSWORD = os.getenv("ESB_PASSWORD")


@functions_framework.cloud_event
def loadToBigQuery(cloud_event: CloudEvent) -> None:
    user = User(mprn=MPRN, username=USERNAME, password=PASSWORD)
    data = fetchCSVData(user, datetime.today() - timedelta(days=5))
    print(data.importData)
