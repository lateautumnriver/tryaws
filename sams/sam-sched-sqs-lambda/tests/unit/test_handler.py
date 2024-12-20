import json

import pytest

from lambda_handlers.hello_world import app


@pytest.fixture()
def sqs_event():
    """
    Generates SQS Event
    """
    body = {
        "RecordNumber": 1234,
        "TimeStamp": "yyyy-mm-ddThh:mm:ss",
        "RequestCode": "AAAA"
    }
    return {
        "Records": [
            {
                "messageId": "059f36b4-87a3-44ab-83d2-661975830a7d",
                "receiptHandle": "AQEBwJnKyrHigUMZj6rYigCgxlaS3SLy0a...",
                "body": json.dumps(body),
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1545082649183",
                    "SenderId": "AIDAIENQZJOLO23YVJ4VO",
                    "ApproximateFirstReceiveTimestamp": "1545082649185"
                },
                "messageAttributes": {},
                "md5OfBody": "e4e68fb7bd0e697a0ae8f1bb342846b3",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-west-2:123456789012:my-queue",
                "awsRegion": "us-west-2"
            },
        ]
    }


def test_lambda_handler(sqs_event):
    ret = app.lambda_handler(sqs_event, "")

    assert 'batchItemFailures' in ret
    assert ret.get('batchItemFailures') is not None
    assert ret.get('batchItemFailures') == []
