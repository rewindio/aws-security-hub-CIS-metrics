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

    start_time = alarm_time - timedelta(minutes=30)
    start_timestamp = round(start_time.timestamp())
    end_time = datetime.datetime.now()
    end_timestamp = round(end_time.timestamp())

    logger.info(f"Start time ({start_time}), end time ({end_time}).")
    logger.info(f"Start timestamp ({start_timestamp}), end timetamps ({end_timestamp}).")

    return {"start": start_timestamp, "end": end_timestamp}
