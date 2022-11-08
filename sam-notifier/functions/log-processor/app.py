r"""
The ``log-processor`` Lambda processes the Events returned by ``log-query``
Lambda. This is required as multiple Log entries can be returned.
"""

import logging
import json
import boto3


dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def event_exists(event_id, table):
    response = table.get_item(Key={'EventId': event_id})
    logger.info("AuditTable query (%s): %s", event_id, response)
    return True if response.get("Item") else False


def process_log_entry(event, table, alarm_type):
    logger.info("Log entry (%s): %s", type(event), event)
    if not event_exists(event.get("eventID"), table):
        logger.info("Storing EventID (%s) in AuditTable.", event.get('eventID'))
        table.put_item(
            Item={
                'EventId': event.get("eventID"),
                'TicketId': None,
                'LogRecord': event,
                'AlarmType': alarm_type
            }
        )
        return event.get("eventID")
    logger.info("Event (%s) has already been processed.", event.get('eventID'))


def lambda_handler(event, context):
    logger.debug("Context: %s", context)

    table = dynamodb.Table(event.get("DDBAuditTableName"))
    new_events = list()

    for log_event in event.get("logs").get("logs"):
        log_event = json.loads(log_event)
        logger.info("Processing log event: %s", log_event.get('eventID'))
        result = process_log_entry(log_event, table, event.get("alarmName"))
        if result:
            new_events.append(result)

    return {
        "events": new_events
    }
