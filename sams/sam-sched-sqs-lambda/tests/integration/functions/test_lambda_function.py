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
        res = self.client.invoke(FunctionName=lambda_function_name)
        assert res is not None
        print(res)
