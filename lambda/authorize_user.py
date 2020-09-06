import os
import json
import boto3
from custom import (
    decode_user_token,
    generate_allow_policy,
    generate_deny_policy,
    parse_cookies
)

db = boto3.resource("dynamodb")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
TABLE_NAME = os.environ.get("TABLE_NAME")
users = db.Table(TABLE_NAME)

def handler(event, context):
    """
    Token must have the format "`Token <token_value>`"
    """

    token = event["authorizationToken"]
    if is_token_right_format(token) is False:
        return generate_deny_policy(None, event["methodArn"], {
            "error": "Token has invalid format"
        })
    token = token.split(" ")[1]
    decode_data = decode_user_token(token, JWT_SECRET_KEY)
    if decode_data["error"] is not None:
        raise Exception("Unauthorized")
    print(decode_data)
    user_id = decode_data["payload"]["user_id"]
    response = users.get_item(
        Key={
            "user_id": user_id
        }
    )
    user = response.get("Item")
    if user is None:
        return generate_deny_policy(None, event["methodArn"], {
            "error": "Token is invalid"
        })
    return generate_allow_policy(user["user_id"], event["methodArn"], {
        "user_id": user["user_id"]
    })


def is_token_right_format(token: str):
    token_parts = token.split(" ")
    if len(token_parts) != 2 or token_parts[0].lower() != "token":
        return False
    return True