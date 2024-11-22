# sam-sched-sqs-lambda

## TODO: Add summary and description.
## TODO: Add pyproject.toml.
## TODO: Arrange tests.

## Local tests

TODO: add how to run a local test by using pytest

## Build

```shell
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
