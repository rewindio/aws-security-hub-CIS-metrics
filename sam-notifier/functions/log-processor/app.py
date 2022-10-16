import logging
import json
import boto3


dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def event_exists(event_id, table):
    response = table.get_item(Key={'EventId': event_id})
    logger.info(f"AuditTable query ({event_id}): {response}")
    return True if response.get("Item") else False


def process_log_entry(event, table, alarm_type):
    logger.info(f"Log entry ({type(event)}): {event}")
    if not event_exists(event.get("eventID"), table):
        logger.info(f"Storing EventID ({event.get('eventID')}) in AuditTable.")
        table.put_item(
            Item={
                'EventId': event.get("eventID"),
                'TicketId': None,
                'LogRecord': event,
                'AlarmType': alarm_type
            }
        )
        return event.get("eventID")
    logger.info(f"Event ({event.get('eventID')}) has already been processed.")


def lambda_handler(event, context):
    table = dynamodb.Table(event.get("DDBAuditTableName"))
    new_events = list()

    for log_event in event.get("logs").get("logs"):
        log_event = json.loads(log_event)
        logger.info(f"Processing log event: {log_event.get('eventID')}")
        result = process_log_entry(log_event, table, event.get("alarmName"))
        if result:
            new_events.append(result)

    return {
        "events": new_events
    }
