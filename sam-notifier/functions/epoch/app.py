r"""
The ``epoch`` Lambda converts the Event date and time to epoch time
as per the Request Parameter for the CloudWatch Log StartQuery call.
"""

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
    logger.debug("Context: %s", context)

    alarm_time = check_time(event)

    logger.info("Event time: %s", alarm_time)

    start_time = alarm_time - timedelta(minutes=10)
    start_timestamp = round(start_time.timestamp())
    end_time = datetime.datetime.now()
    end_timestamp = round(end_time.timestamp())

    logger.info("Start time (%s), end time (%s).", start_time, end_time)
    logger.info(
        "Start timestamp (%s), end timetamps (%s).", start_timestamp, end_timestamp
    )

    return {"start": start_timestamp, "end": end_timestamp}
