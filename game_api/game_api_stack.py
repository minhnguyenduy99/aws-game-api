from aws_cdk import (
    core, 
    aws_dynamodb,
    aws_apigateway,
    aws_lambda
)
import os
import api_models as models

LIBRARY_PATH = os.path.abspath(".env/Lib/site-packages")


class GameApiStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        pyjwt_layer = aws_lambda.LayerVersion(
            self,
            "minhnd-pyjwt",
            code=aws_lambda.Code.from_asset(os.path.join(LIBRARY_PATH, 'jwt')),
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_8]
        )

        # Login
        lambda_login = aws_lambda.Function(
            self,
            "minh.demo-login",
            code=aws_lambda.Code.from_asset("./lambda"),
            handler="login.handler",
            layers=[pyjwt_layer],
            function_name="minh-demo-login",
            runtime=aws_lambda.Runtime.PYTHON_3_8
        )

        login_api = aws_apigateway.LambdaRestApi(
            self,
            "minh-intern-UserLogin",
            handler=lambda_login,
            proxy=False,
            endpoint_types=[aws_apigateway.EndpointType.REGIONAL]
        )

        login_lambda_integration = aws_apigateway.LambdaIntegration(
            lambda_login,
            proxy=True
        )

        login_model = login_api.add_model("UserLoginModel", **models.login_model)

        login_api.root.add_resource('login').add_method(
            'POST', 
            integration=login_lambda_integration,
            request_validator_options={
                "validate_request_body": True
            },
            request_models={
                "application/json": login_model
            }
        )


        


