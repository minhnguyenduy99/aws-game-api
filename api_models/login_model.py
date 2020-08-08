from aws_cdk.aws_apigateway import (ModelOptions, JsonSchemaType, JsonSchemaVersion)

login_model = {
    "model_name": "UserLoginModel",
    "content_type": "application/json",
    "schema": {
        "schema": JsonSchemaVersion.DRAFT4,
        "title": "Login user request",
        "type": JsonSchemaType.OBJECT,
        "properties": {
            "username": {
                "type": JsonSchemaType.STRING
            },
            "password": {
                "type": JsonSchemaType.STRING
            }
        },
        "required": ["username", "password"]
    }
}