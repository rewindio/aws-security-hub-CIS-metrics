r"""
The ``create-ticket`` Lambda retrieves the Event details from the
DynamoDB table and creates a Jira issue.
"""

import logging
import json
import requests

import boto3
from botocore.exceptions import ClientError


dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_secret(jira_auth_token_secret_arn):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager'
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=jira_auth_token_secret_arn
        )
    except ClientError as err:
        logger.error(
            "Error, unable to access Secret '%s'.", jira_auth_token_secret_arn)
        logger.error(err)

    if 'SecretString' in get_secret_value_response:
        return get_secret_value_response['SecretString']


def get_jira_auth_header(jira_auth_token_secret_arn):
    headers = {
        "Authorization": f"Basic {get_secret(jira_auth_token_secret_arn)}",
        "Content-Type": "application/json"
    }
    return headers


def create_jira_issue(jira_url, headers, issue_data):
    resp = requests.post(f"{jira_url}/issue/", headers=headers,
                         data=json.dumps(issue_data), timeout=60)
    logger.info("Jira Response: %s (%s)", resp, resp.url)

    if resp.status_code == 201 or resp.status_code == requests.codes.ok: #pylint: disable=E1101
        ticket = resp.json()
        logger.info("Successfully created ticket: %s", ticket.get('key'))
        return ticket.get('key')


def get_ddb_event(event_id, table):
    logger.info("Get EventID: %s, DynamoDB table: %s", event_id, table)
    try:
        response = table.get_item(Key={'EventId': event_id})
    except ClientError as err:
        logger.error(
            "Couldn't get event %s from table %s. Here's why: %s: %s",
            event_id, table.name,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise
    else:
        return response['Item']


def update_ddb_event(event_id, ticket_id, table):
    logger.info(
        "Update EventID: %s, Ticket: %s, DynamoDB table: %s", event_id, ticket_id, table)
    try:
        response = table.update_item(
            Key={'EventId': event_id},
            UpdateExpression='SET TicketId=:newTicketId',
            ExpressionAttributeValues={
                ':newTicketId': ticket_id
            },
            ReturnValues="UPDATED_NEW"
        )
    except ClientError as err:
        logger.error(
            "Couldn't update event %s from table %s. Here's why: %s: %s",
            ticket_id, table.name,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise
    else:
        return response


def process_log_record(log_record, jira_project_key, alarm_name):
    logger.info("LogRecord (%s): %s", type(log_record), log_record)
    issue_data = {
        "fields": {
            "project":
            {
                "key": jira_project_key
            },
            "summary": f"{alarm_name} ({log_record.get('eventID')})",
            "description": None,
            "issuetype": {
                "name": "Task"
            }
        }
    }

    formatted = f"Alarm Name: {alarm_name} \n"
    formatted = f"Event  ID: {log_record.get('eventID')}) \n\n"

    event_details = "Event Details \n"
    user_details = "User Details \n"
    additional_details = "Additional Details \n"

    for key, val in log_record.items():
        if key in ("eventID", "eventVersion"):
            # Skipping these Event entries
            continue

        if key in (
            "eventName", "errorMessage", "eventSource",
            "eventTime", "eventType", "eventCategory"
        ):
            event_details += f"{key}: {val if val else 'NO_VALUE_SPECIFIED'} \n"
            continue

        if key == "userIdentity":
            for key, val in log_record.get("userIdentity").items():
                user_details += f"{key}: {val if val else 'NO_VALUE_SPECIFIED'} \n"
            continue

        if key in ("sourceIPAddress", "userAgent", "recipientAccountId", "awsRegion"):
            user_details += f"{key}: {val if val else 'NO_VALUE_SPECIFIED'} \n"
            continue

        additional_details += f"{key}: {val if val else 'NO_VALUE_SPECIFIED'} \n"

    formatted += f"{event_details} \n"
    formatted += f"{user_details} \n"
    formatted += f"{additional_details} \n"

    issue_data["fields"]["description"] = formatted
    return issue_data


def lambda_handler(event, context):
    logger.debug("Context: %s", context)

    table = dynamodb.Table(event.get("DDBAuditTableName"))

    jira_url = event.get("JiraUrl")
    jira_project_key = event.get("JiraProjectKey")
    jira_auth_token_secret_arn = event.get("JiraAuthTokenSecretArn")

    logger.info("Event: %s", event)

    alarm_name = event.get("alarmName", "AWS CIS Benchmark Alarm")
    ticket_id = None

    if event.get("EventId"):
        event_record = get_ddb_event(event.get("EventId"), table)
        logger.info("Event record: %s", event_record)

        if event_record.get("LogRecord"):
            jira_issue_data = process_log_record(
                event_record.get("LogRecord"), jira_project_key, alarm_name)
            logger.info("Jira Issue Data payload: %s", jira_issue_data)
            ticket_id = create_jira_issue(jira_url, get_jira_auth_header(
                jira_auth_token_secret_arn), jira_issue_data)
            update_ddb_event(event.get("EventId"), ticket_id, table)

    return {
        "TicketID": ticket_id
    }
