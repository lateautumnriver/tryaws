"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test.
"""
import os
import time

import boto3
import pytest


def get_stack_name() -> str:
    """
    Get the name of the stack we are going to test.
    """
    return os.environ.get("AWS_SAM_STACK_NAME")


def get_stack_outputs(stack_name: str) -> dict:
    """
    Get the stack outputs from AWS CloudFormation stack
    """
    if stack_name is None:
        raise ValueError('Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack')

    client = boto3.client("cloudformation")

    try:
        response = client.describe_stacks(StackName=stack_name)
    except Exception as e:
        raise Exception(
            f"Cannot find stack {stack_name} \n" f'Please make sure a stack with the name "{stack_name}" exists'
        ) from e

    stacks = response["Stacks"]
    return stacks[0]["Outputs"]


def get_output_value_from_stack(stack_name: str, key_name: str) -> str:
    """
    Get the output value from AWS CloudFormation stack
    """
    stack_outputs = get_stack_outputs(stack_name)
    data = [output for output in stack_outputs if output["OutputKey"] == key_name]

    if not data:
        raise KeyError(f"{key_name} not found in stack {stack_name}")

    return data[0]["OutputValue"]


@pytest.fixture()
def queue_name():
    """
    Get the queue name from AWS CloudFormation stack
    """
    return get_output_value_from_stack(get_stack_name(), 'MyFifoQueueName')


@pytest.fixture()
def queue_url():
    """
    Get the queue url from AWS CloudFormation stack
    """
    return get_output_value_from_stack(get_stack_name(), 'MyFifoQueueUrl')


def remove_all_messages_in_the_queue():
    """
    Remove all messages from the queue
    """
    sqs = boto3.resource('sqs')
    queue_name = get_output_value_from_stack(get_stack_name(), 'MyFifoQueueName')
    queue = sqs.get_queue_by_name(QueueName=queue_name)
    for message in queue.receive_messages(MaxNumberOfMessages=10, WaitTimeSeconds=10):
        message.delete()


@pytest.fixture(scope='session', autouse=True)
def fixture_by_session():
    """
    Fixture by a session
    """
    remove_all_messages_in_the_queue()
    yield
    # Since the retention period of the queue is 60, wait for that time for the following tests.
    time.sleep(60)
