"""
Test for a queue
"""
import time
import uuid
from datetime import datetime, timezone

import boto3
import pytest
from botocore.exceptions import ClientError


class TestQueue:
    sqs = boto3.resource('sqs')

    def test_queue_exists(self, queue_name, queue_url):
        """
        Test if the queue name exists.
        """
        queue = self.sqs.get_queue_by_name(QueueName=queue_name)
        assert queue.url == queue_url

    def test_queue_does_not_exist(self):
        """
        Test if the queue name does not exist.
        """
        with pytest.raises(ClientError) as ex_info:
            self.sqs.get_queue_by_name(QueueName='no-such-queue')
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

    def test_sending_a_message(self, queue_name):
        """
        Test sending a message to the queue and receiving a message from the queue.
        """
        body = uuid.uuid4().hex
        queue = self.sqs.get_queue_by_name(QueueName=queue_name)
        # sending
        sent = queue.send_message(MessageBody=body, MessageGroupId='message-group-id')
        assert type(sent) == dict
        assert 'MD5OfMessageBody' in sent
        assert 'MessageId' in sent
        assert 'SequenceNumber' in sent
        # receiving
        messages = queue.receive_messages()
        assert len(messages) == 1
        message = messages.pop()
        assert message.body == body
        message.delete()

    def test_receiving_a_message_with_attributes(self, queue_name):
        """
        Test receiving a message with attributes from the queue.
        """
        body = uuid.uuid4().hex
        queue = self.sqs.get_queue_by_name(QueueName=queue_name)
        # sending
        message_attributes = {
            # TODO: set custom attributes then test them when receiving.
        }
        sent = queue.send_message(
            MessageBody=body,
            MessageGroupId='message-group-id',
            MessageAttributes=message_attributes
        )
        assert 'MessageId' in sent
        message_id = sent.get('MessageId')
        # receiving
        messages = queue.receive_messages(
            MessageSystemAttributeNames=['All']
        )
        assert len(messages) == 1
        message = messages.pop()
        # For SQS.Message,
        # see https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs/message/index.html#SQS.Message
        assert message.body == body
        assert message.message_id == message_id
        attributes = message.attributes
        assert 'ApproximateFirstReceiveTimestamp' in attributes
        assert 'ApproximateReceiveCount' in attributes
        assert 'MessageDeduplicationId' in attributes
        assert 'MessageGroupId' in attributes
        assert 'SenderId' in attributes
        assert 'SentTimestamp' in attributes
        assert 'SequenceNumber' in attributes
        assert attributes.get('MessageGroupId') == 'message-group-id'
        message.delete()

    def test_message_is_received_one_by_one_because_of_batch_size(self, queue_name):
        """
        Test if the number of items that are received is 1 since EventSourceMapping.BatchSize is 1.
        Test if a message is received when MessageGroupId is different.
        """
        queue = self.sqs.get_queue_by_name(QueueName=queue_name)
        # sending
        groups = [1, 2, 3]
        bodies = []
        for group in groups:
            body = uuid.uuid4().hex
            bodies.append(body)
            group_id = f'message-group-id-{group}'
            queue.send_message(MessageBody=body, MessageGroupId=group_id)
        # receiving
        for expected in bodies:
            messages = queue.receive_messages()
            assert len(messages) == 1
            message = messages.pop()
            assert message.body == expected
            message.delete()

    def test_following_messages_in_the_same_group_are_not_received_when_a_previous_message_in_the_queue(self,
                                                                                                        queue_name):
        """
        Test if no following message is received when a previous message with the same MessageGroupId remains in the queue.
        """
        queue = self.sqs.get_queue_by_name(QueueName=queue_name)

        # sending 2 messages with the same message group id
        expected_bodies = []
        for idx in [1, 2]:
            body = uuid.uuid4().hex
            expected_bodies.append(body)
            queue.send_message(MessageBody=body, MessageGroupId='message-group-id')

        # receiving 1st is OK
        messages = queue.receive_messages()
        assert len(messages) == 1
        message = messages.pop()
        assert message.body == expected_bodies[0]

        # receiving 2nd takes for a while
        start_at = datetime.now(timezone.utc)
        messages = queue.receive_messages(WaitTimeSeconds=1)
        end_at = datetime.now(timezone.utc)
        assert (end_at - start_at).total_seconds() >= 1
        assert (end_at - start_at).total_seconds() < 2
        assert len(messages) == 0
        # assert message.body == expected_bodies[0]

        # delete the first message
        message.delete()

        # receiving 3rd time is OK since the first message was deleted
        messages = queue.receive_messages(WaitTimeSeconds=0)
        assert len(messages) == 1
        message = messages.pop()
        assert message.body == expected_bodies[1]
        message.delete()

    def test_message_with_the_same_body_is_received_when_different_duplication_id(self, queue_name):
        """
        Test if a message with the same body is received when MessageDeduplicationId is different.
        """
        queue = self.sqs.get_queue_by_name(QueueName=queue_name)

        body = uuid.uuid4().hex
        # sending 1
        sent1 = queue.send_message(
            MessageBody=body,
            MessageGroupId='message-group-id-1',
            MessageDeduplicationId=uuid.uuid4().hex,
        )
        # sending 2
        sent2 = queue.send_message(
            MessageBody=body,
            MessageGroupId='message-group-id-2',
            MessageDeduplicationId=uuid.uuid4().hex,
        )

        # receiving 1
        messages = queue.receive_messages(
            WaitTimeSeconds=1,
            MessageSystemAttributeNames=['All']
        )
        assert len(messages) == 1
        message1 = messages.pop()
        assert message1.body == body

        # receiving 2
        messages = queue.receive_messages(
            WaitTimeSeconds=1,
            MessageSystemAttributeNames=['All']
        )
        assert len(messages) == 1
        message2 = messages.pop()
        assert message2.body == body

        # clean up
        message1.delete()
        message2.delete()

    def test_no_message_is_received_even_if_different_message_group_when_the_same_duplication_id(self, queue_name):
        """
        Test if no message is received when using the same message duplication id even if different message group id is used.
        """
        queue = self.sqs.get_queue_by_name(QueueName=queue_name)
        # Sending
        groups = [1, 2]
        body = uuid.uuid4().hex
        for group in groups:
            group_id = f'message-group-id-{group}'
            queue.send_message(MessageBody=body, MessageGroupId=group_id)

        # The first message is received.
        messages = queue.receive_messages(WaitTimeSeconds=0)
        assert len(messages) == 1
        message = messages.pop()
        assert message.body == body

        # No message is received for the 2nd retrieval due to a duplicate message.
        messages = queue.receive_messages(WaitTimeSeconds=0)
        assert len(messages) == 0

        # Delete the first message
        message.delete()

        # No message is received even if the first message was deleted.
        messages = queue.receive_messages(WaitTimeSeconds=1)
        assert len(messages) == 0

        time.sleep(10)

        # After 10 seconds, visibility timeout expires but no message is received because of duplication.
        messages = queue.receive_messages(WaitTimeSeconds=1)
        assert len(messages) == 0

    def test_messages_are_deleted_after_retention_period(self, queue_name):
        """
        Test if a message is deleted after MessageRetentionPeriod passed.
        """
        body = uuid.uuid4().hex
        queue = self.sqs.get_queue_by_name(QueueName=queue_name)

        # sending
        queue.send_message(MessageBody=body, MessageGroupId='message-group-id')

        # receiving
        messages = queue.receive_messages(WaitTimeSeconds=0)
        assert len(messages) == 1
        message = messages.pop()
        assert message.body == body

        # After 60 seconds, the message is deleted due to MessageRetentionPeriod.
        time.sleep(60)
        messages = queue.receive_messages(WaitTimeSeconds=0)
        assert len(messages) == 0

    def test_received_message_order_consistent_in_a_group(self, queue_name):
        """
        Test if message order is consistent in a group.
        """
        queue = self.sqs.get_queue_by_name(QueueName=queue_name)

        # Sending
        queue.send_message(MessageBody='group1, message1', MessageGroupId='group-1', MessageDeduplicationId=uuid.uuid4().hex)
        queue.send_message(MessageBody='group1, message2', MessageGroupId='group-1', MessageDeduplicationId=uuid.uuid4().hex)

        # Receiving
        messages = queue.receive_messages(MaxNumberOfMessages=10, WaitTimeSeconds=1)
        assert len(messages) == 2
        assert messages[0].body == 'group1, message1'
        assert messages[1].body == 'group1, message2'

        # Clean up
        for message in messages:
            message.delete()

    def test_receiving_a_message_takes_wait_time_seconds_when_no_messages(self, queue_name):
        """
        Test if receiving a message takes 10 seconds when no message in the queue since ReceiveMessageWaitTimeSeconds is 10.
        """
        queue = self.sqs.get_queue_by_name(QueueName=queue_name)
        # receiving yet no messages
        start_at = datetime.now(timezone.utc)
        messages = queue.receive_messages()
        assert len(messages) == 0
        end_at = datetime.now(timezone.utc)
        assert (end_at - start_at).total_seconds() >= 10
        assert (end_at - start_at).total_seconds() < 11
