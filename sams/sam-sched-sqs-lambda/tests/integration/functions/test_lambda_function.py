import json

import boto3


class TestLambdaFunction:
    client = boto3.client('lambda')

    def test_function_exists(self, lambda_function_name):
        """
        Test if the function name exists.
        """
        func = self.client.get_function(FunctionName=lambda_function_name)
        assert func is not None

    def test_function_invocation(self, lambda_function_name):
        """
        Test the function invocation.
        """
        expected = {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Record is not a SQS event',
            })
        }
        res = self.client.invoke(FunctionName=lambda_function_name)
        assert res is not None
        assert 'Payload' in res
        payload = res.get('Payload').read().decode('utf-8')
        assert payload is not None
        actual = json.loads(payload)
        assert actual == expected
        return
        payload = json.loads(res["Payload"].read())
        # assert 'FunctionError' in res
        # assert 'LogResult' in res
        assert 'batchItemFailures' in payload
        assert payload.get('batchItemFailures') is not None
        assert payload.get('batchItemFailures') == []

