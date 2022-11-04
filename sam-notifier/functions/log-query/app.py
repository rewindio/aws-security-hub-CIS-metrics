import time
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client('logs')


def get_query_results(query_id):
    response = client.get_query_results(
        queryId=query_id
    )

    logger.info(f"Get Query Results: {response}")

    # Wait for the Query to complete
    while response.get("status") in ("Running", "Scheduled"):
        time.sleep(5)
        response = client.get_query_results(
            queryId=query_id
        )
        if response.get("status") == "Complete":
            logger.info(f"Query results: {response}")
            logger.info(f"Query statistics: {response.get('statistics')}")
        else:
            logger.error(f"CloudWatch Query failed. {response.get('status')}")
    return response


def process_query_results(results):
    log_entries = list()
    logger.info(f"Process Query Results: {results}")
    for result in results.get("results"):
        for entry in result:
            if entry.get("field") == "@message":
                logger.info(entry.get("value"))
                log_entries.append(entry.get("value"))
    return log_entries


def lambda_handler(event, context):
    log_group_name = event.get("CloudWatchLogsLogGroupName")

    logger.info(f"StartTime: {event.get('epoch').get('start')}")
    logger.info(f"EndTime: {event.get('epoch').get('end')}")
    logger.info(f"QueryString: {event.get('query').get('string')}")
    logger.info(f"LogGroupName: {log_group_name}")

    response = client.start_query(
        logGroupName=log_group_name,
        startTime=event.get("epoch").get("start"),
        endTime=event.get("epoch").get("end"),
        queryString=event.get("query").get("string"),
        limit=10
    )

    logger.info(f"Response: {response}")
    logger.info(f"CloudWatch Logs QueryId: {response.get('queryId')}")

    results = get_query_results(response.get("queryId"))
    logs = process_query_results(results)

    # Raise AssertionError if CloudWatch Logs query returned zero logs
    assert len(logs) >= 1, "CloudWatch Logs query did not return any entries."

    return {
        "logs": logs
    }
