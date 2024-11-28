"""
Test for a queue
"""

import boto3
import pytest
from botocore.exceptions import ClientError


class TestQueue:
    client = boto3.client('sqs')

    def test_queue_exists(self, queue_name, queue_url):
        """
        Test if the queue name exists.
        """
        res = self.client.get_queue_url(QueueName=queue_name)
        assert 'QueueUrl' in res
        assert res.get('QueueUrl') == queue_url

    def test_queue_does_not_exist(self):
        """
        Test if the queue name does not exist.
        """
        with pytest.raises(ClientError) as ex_info:
            self.client.get_queue_url(QueueName='no-such-queue')
        ex = ex_info.value
        assert 'Error' in ex.response
        assert 'ResponseMetadata' in ex.response
        expected = {
            'Message': 'The specified queue does not exist.',
            'Code': 'AWS.SimpleQueueService.NonExistentQueue',
            'QueryErrorCode': 'QueueDoesNotExist',
            'Type': 'Sender'
        }
        assert ex.response.get('Error') == expected

    def test_sending_a_message(self, queue_url):
        """
        Test sending a message to the queue and receiving a message from the queue.
        """
        sent = self.client.send_message(QueueUrl=queue_url, MessageBody='test message', MessageGroupId='message-group-id')
        assert 'MD5OfMessageBody' in sent
        # assert 'MD5OfMessageAttributes' in res
        # assert 'MD5OfMessageSystemAttributes' in res
        assert 'MessageId' in sent
        assert 'SequenceNumber' in sent

        recv = self.client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)
        import pprint
        pprint.pprint(recv)
        assert len(recv.get('Messages')) == 1
        actual_message = recv.get('Messages').pop()
        assert actual_message == 'test message'
        receipt_handle = actual_message.get('ReceiptHandle')
        assert receipt_handle == sent['MessageId']
        self.client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

    # * Test if receiving a message takes 10 seconds when no message in the queue since ReceiveMessageWaitTimeSeconds is 10.

    # TODO: Add testcases
    # * Test if the function is invoked when a message is sent to the queue.
    # * Test if the number of items that are received is 1 since EventSourceMapping.BatchSize is 1.
    # * Test if a message is received when MessageGroupId is different.
    # * Test if no following message is received when a message with the same MessageGroupId remains in the queue.
    # * Test when MessageDeduplicationId is specified. Should I project it?
    # * Test if the function is invoked again after the visibility timeout of the queue when batchItemFailure is not empty.
    # * Test if the message is deleted from the queue after the function is finished when batchItemFailure is empty.
    # * Test if a message is deleted after MessageRetentionPeriod passed.
    # * Test if the function is immediately invoked since DelaySeconds is 0.
    # * Test for ScalingConfig.MaximumConcurrency
