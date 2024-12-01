"""
For a best practice of using SQS invoking a Lambda function,
see https://docs.aws.amazon.com/prescriptive-guidance/latest/lambda-event-filtering-partial-batch-responses-for-sqs/welcome.html

For using event filtering with an Amazon SQS event source
see https://docs.aws.amazon.com/lambda/latest/dg/with-sqs-filtering.html
"""
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('tryaws.sams.sam-sched-sqs-lambda')


def lambda_handler(event, context):
    """
    See https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html
    For troubleshooting,
    see also https://repost.aws/knowledge-center/lambda-sqs-report-batch-item-failures
    """
    logger.info("Received event", event)

    if 'Records' not in event:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Record is not a SQS event',
            })
        }

    batch_item_failures = []
    sqs_batch_response = {}

    for record in event["Records"]:
        try:
            pass
        except Exception as e:
            batch_item_failures.append({"itemIdentifier": record['messageId']})

    sqs_batch_response["batchItemFailures"] = batch_item_failures
    # Lambda treats a batch as a complete success if your function returns any of the following:
    #  * An empty batchItemFailures list
    #  * A null batchItemFailures list
    #  * An empty EventResponse
    #  * A null EventResponse
    # Lambda treats a batch as a complete failure if your function returns any of the following:
    #  * An invalid JSON response
    #  * An empty string itemIdentifier
    #  * A null itemIdentifier
    #  * An itemIdentifier with a bad key name
    #  * An itemIdentifier value with a message ID that doesn't exist
    return sqs_batch_response


"""
# CloudWatch metrics
To determine whether your function is correctly reporting batch item failures,
you can monitor the NumberOfMessagesDeleted and ApproximateAgeOfOldestMessage Amazon SQS metrics in Amazon CloudWatch.
 * NumberOfMessagesDeleted tracks the number of messages removed from your queue.
   If this drops to 0, this is a sign that your function response is not correctly returning failed messages.
 * ApproximateAgeOfOldestMessage tracks how long the oldest message has stayed in your queue.
   A sharp increase in this metric can indicate that your function is not correctly returning failed messages.
"""
