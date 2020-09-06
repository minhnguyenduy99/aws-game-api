from aws_cdk.aws_apigateway import (JsonSchemaType, JsonSchemaVersion)

update_user_model = {
    "model_name": "UpdateUserModel",
    "content_type": "application/json",
    "schema": {
        "schema": JsonSchemaVersion.DRAFT4,
        "title": "Update user model",
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