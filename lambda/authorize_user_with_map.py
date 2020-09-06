import os
import json
import boto3
from custom import decode_user_token

db = boto3.resource("dynamodb")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
TABLE_NAME = os.environ.get("TABLE_NAME")
users = db.Table(TABLE_NAME)

def handler(event, context):
    token = event["authorizationToken"]
    decode_data = decode_user_token(token, JWT_SECRET_KEY)
    if decode_data["error"] is not None:
        return generate_deny_policy(event, {
            "error": decode_data["error"]
        })
    user_id = decode_data["payload"]["user_id"]
    response = users.get_item(
        Key={
            "user_id": user_id
        }
    )
    user = response.get("Item")
    if user is None:
        return generate_deny_policy(event, {
            "error": "Token is invalid"
        })
    return generate_allow_policy(event, user["user_id"], {
        "user_id": user["user_id"]
    })


def generate_deny_policy(event, context = {}):
    return {
        "principalId": None,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Deny",
                    "Resource": event["methodArn"]
                }
            ]
        },
        "context": context
    }


def generate_allow_policy(event, principal, context = {}):
    return {
        "principalId": principal,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": event["methodArn"]
                }
            ]
        },
        "context": context
    }
