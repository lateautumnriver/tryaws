"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test.
"""
import os

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
def lambda_function_name():
    """
    Get the function name from AWS CloudFormation stack
    """
    return get_output_value_from_stack(get_stack_name(), 'HelloWorldFunctionName')


@pytest.fixture()
def queue_name():
    """
    Get the queue name from AWS CloudFormation stack
    """
    return get_output_value_from_stack(get_stack_name(), 'InvokeHelloWorldFifoQueueName')


@pytest.fixture()
def queue_url():
    """
    Get the queue url from AWS CloudFormation stack
    """
    return get_output_value_from_stack(get_stack_name(), 'InvokeHelloWorldFifoQueueUrl')
