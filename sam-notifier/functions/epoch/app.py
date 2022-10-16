import logging

import datetime
from datetime import timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def check_time(event):
    if event.get("time"):
        return datetime.datetime.strptime(event.get("time"), "%Y-%m-%dT%H:%M:%SZ")
    return datetime.datetime.now()


def lambda_handler(event, context):
    alarm_time = check_time(event)

    logger.info(f"Event time: {alarm_time}")

    start = round((alarm_time - timedelta(minutes=30)).timestamp())
    end = round(alarm_time.timestamp())

    logger.info(f"Start timestamp ({start}), end timetamps ({end}).")

    return {"start": start, "end": end}
