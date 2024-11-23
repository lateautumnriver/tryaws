"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test.
"""
import os

import boto3
import pytest


def get_stack_name() -> str:
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


@pytest.fixture()
def lambda_function_name():
    """
    Get the function name from AWS CloudFormation stack
    """
    stack_name = get_stack_name()
    stack_outputs = get_stack_outputs(stack_name)
    data = [output for output in stack_outputs if output["OutputKey"] == "HelloWorldFunctionName"]

    if not data:
        raise KeyError(f"HelloWorldFunctionName not found in stack {stack_name}")

    return data[0]["OutputValue"]
