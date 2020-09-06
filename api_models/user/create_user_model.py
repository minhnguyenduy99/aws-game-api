from aws_cdk.aws_apigateway import (JsonSchemaType, JsonSchemaVersion)

create_user_model = {
    "model_name": "CreateUserModel",
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
            },
            "email": {
                "type": JsonSchemaType.STRING,
                "pattern": "(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+$)"
            },
            "profile": {
                "type": JsonSchemaType.OBJECT,
                "family_name": {
                    "type": JsonSchemaType.STRING
                },
                "given_name": {
                    "type": JsonSchemaType.STRING
                },
                "social_id": {
                    "type": JsonSchemaType.STRING
                }
            }
        },
        "required": ["username", "password", "email", "profile"]
    }
}