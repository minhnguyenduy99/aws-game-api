from aws_cdk.aws_apigateway import (JsonSchemaType, JsonSchemaVersion)

profile_model = {
    "model_name": "ProfileModel",
    "content_type": "application/json",
    "schema": {
        "schema": JsonSchemaVersion.DRAFT4,
        "title": "Profile model",
        "type": JsonSchemaType.OBJECT,
        "properties": {
            "family_name": {
                "type": JsonSchemaType.STRING
            },
            "given_name": {
                "type": JsonSchemaType.STRING
            }
        },
        "required": ["family_name", "given_name"]
    }
}