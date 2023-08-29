import re
import json
import csv

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict

from bs4 import BeautifulSoup
from requests import Session


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
}

ACCOUNT_PAGE = "https://myaccount.esbnetworks.ie/"
LOGIN_API = "https://login.esbnetworks.ie/esbntwkscustportalprdb2c01.onmicrosoft.com/B2C_1A_signup_signin"
SETTINGS_REGEX = r"(?<=var SETTINGS = )\S*;"


class READ_TYPE(Enum):
    IMPORT = "Active Import Interval (kW)"
    EXPORT = "Active Export Interval (kW)"


@dataclass
class User:
    mprn: str
    username: str
    password: str


@dataclass
class MeterData:
    # Maps: datetime string -> meter read value
    importData: Dict[str, float] = field(default_factory=dict)
    exportData: Dict[str, float] = field(default_factory=dict)


def login(user: User) -> Session:
    s = Session()
    s.headers.update(DEFAULT_HEADERS)
    login = s.get(ACCOUNT_PAGE, allow_redirects=True)
    settingsRaw = re.findall(SETTINGS_REGEX, str(login.content))
    settings = json.loads(settingsRaw[0][:-1])

    req = s.post(
        f"{LOGIN_API}/SelfAsserted?tx={settings['transId']}&p=B2C_1A_signup_signin",
        data={
            "signInName": user.username,
            "password": user.password,
            "request_type": "RESPONSE",
        },
        headers={"x-csrf-token": settings["csrf"]},
        allow_redirects=False,
    )
    req.raise_for_status()

    return confirmLogInCSRF(s, settings["transId"], settings["csrf"])


def confirmLogInCSRF(s: Session, transactionID: str, csrfToken: str) -> Session:
    confirmation = s.get(
        f"{LOGIN_API}/api/CombinedSigninAndSignup/confirmed",
        params={
            "rememberMe": False,
            "csrf_token": csrfToken,
            "tx": transactionID,
            "p": "B2C_1A_signup_signin",
        },
    )
    confirmation.raise_for_status()

    soup = BeautifulSoup(confirmation.content, "html.parser")
    form = soup.find("form", {"id": "auto"})
    req = s.post(
        form["action"],
        allow_redirects=False,
        data={
            "state": form.find("input", {"name": "state"})["value"],
            "client_info": form.find("input", {"name": "client_info"})["value"],
            "code": form.find("input", {"name": "code"})["value"],
        },
    )
    req.raise_for_status()

    return s


def fetchCSVData(user: User, startDate: datetime) -> MeterData:
    s = login(user)
    data = s.get(
        f"{ACCOUNT_PAGE}/DataHub/DownloadHdf?mprn={user.mprn}&startDate={startDate.strftime('%Y-%m-%d')}"
    )
    entryList = data.content.decode("utf-8").splitlines()
    # Parse all except header row
    reader = csv.DictReader(entryList)

    meterData = MeterData()
    for row in reader:
        if row["Read Type"] == READ_TYPE.IMPORT.value:
            meterData.importData[row["Read Date and End Time"]] = float(
                row["Read Value"]
            )
        elif row["Read Type"] == READ_TYPE.EXPORT.value:
            meterData.exportData[row["Read Date and End Time"]] = float(
                row["Read Value"]
            )
    return meterData
