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
    except ClientError as e:
        logger.error(
            f"Error, unable to access Secret '{jira_auth_token_secret_arn}'.")
        logger.error(e)

    if 'SecretString' in get_secret_value_response:
        return get_secret_value_response['SecretString']


def get_jira_auth_header(jira_auth_token_secret_arn):
    headers = {
        "Authorization": f"Basic {get_secret(jira_auth_token_secret_arn)}",
        "Content-Type": "application/json"
    }
    return headers


def create_jira_issue(jira_url, headers, issue_data):
    r = requests.post(f"{jira_url}/issue/", headers=headers,
                      data=json.dumps(issue_data))
    logger.info(f"Jira Response: {r} ({r.url})")

    if r.status_code == 201 or r.status_code == requests.codes.ok:
        ticket = r.json()
        logger.info(f"Successfully created ticket: {ticket.get('key')}")
        return ticket.get('key')


def get_ddb_event(event_id, table):
    logger.info(f"Get EventID: {event_id}, DynamoDB table: {table}")
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
        f"Update EventID: {event_id}, Ticket: {ticket_id}, DynamoDB table: {table}")
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
    logger.info(f"LogRecord ({type(log_record)}): {log_record}")
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

    for k, v in log_record.items():
        if k in ("eventID", "eventVersion"):
            # Skipping these Event entries
            continue

        if k in ("eventName", "errorMessage", "eventSource", "eventTime", "eventType", "eventCategory"):
            event_details += f"{k}: {v if v else 'NO_VALUE_SPECIFIED'} \n"
            continue

        if k == "userIdentity":
            for k, v in log_record.get("userIdentity").items():
                user_details += f"{k}: {v if v else 'NO_VALUE_SPECIFIED'} \n"
            continue

        if k in ("sourceIPAddress", "userAgent", "recipientAccountId", "awsRegion"):
            user_details += f"{k}: {v if v else 'NO_VALUE_SPECIFIED'} \n"
            continue

        additional_details += f"{k}: {v if v else 'NO_VALUE_SPECIFIED'} \n"

    formatted += f"{event_details} \n"
    formatted += f"{user_details} \n"
    formatted += f"{additional_details} \n"

    issue_data["fields"]["description"] = formatted
    return issue_data


def lambda_handler(event, context):
    table = dynamodb.Table(event.get("DDBAuditTableName"))

    jira_url = event.get("JiraUrl")
    jira_project_key = event.get("JiraProjectKey")
    jira_auth_token_secret_arn = event.get("JiraAuthTokenSecretArn")

    logger.info(f"Event: {event}")

    alarm_name = event.get("alarmName", "AWS CIS Benchmark Alarm")
    ticket_id = None

    if event.get("EventId"):
        event_record = get_ddb_event(event.get("EventId"), table)
        logger.info(f"Event record: {event_record}")

        if event_record.get("LogRecord"):
            jira_issue_data = process_log_record(
                event_record.get("LogRecord"), jira_project_key, alarm_name)
            logger.info(f"Jira Issue Data payload: {jira_issue_data}")
            ticket_id = create_jira_issue(jira_url, get_jira_auth_header(
                jira_auth_token_secret_arn), jira_issue_data)
            update_ddb_event(event.get("EventId"), ticket_id, table)

    return {
        "TicketID": ticket_id
    }
