# sam-sched-sqs-lambda

## TODO: Add summary and description.

## Prerequisites

* AWS CLI
* SAM CLI

## Local environment

```shell
# When using python3.11
python3.11 -mvenv venv

# Activate venv
source venv/bin/activate

# Confirm it.
python -V
# Python 3.11.10
```

### Package installation

```shell
# For src
pip install -r liblayer/requirements.txt

# For tests
pip install -r tests/requirements.txt
```

## Local tests

```shell
source venv/bin/activate

# Run all tests
python -mpytest tests
```

## Build

```shell
# When using a docker
sam build --use-container
```

## Deploy

```shell
APP_ENV='dev'
sam deploy --config-env "${APP_ENV}"
```

## Cleanup

To delete the sample application that you created, use the AWS CLI. Assuming you used your project name for the stack name, you can run the following:

```bash
sam delete --stack-name "sam-sched-sqs-lambda"
```
