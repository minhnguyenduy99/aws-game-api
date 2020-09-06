import json
import boto3
import jwt
import os
import uuid
import bcrypt
db = boto3.resource("dynamodb")
USER_TABLE_NAME = os.environ.get("TABLE_NAME")
users = db.Table(USER_TABLE_NAME)


def handler(event, context):
    requested_user_id = event["pathParameters"]["user_id"]
    user_id = event["requestContext"]["authorizer"]["user_id"]
    payload = json.loads(event["body"])
    if requested_user_id != user_id:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Unauthorized"
            })
        }
    # Check if user id exists
    response = users.get_item(
        Key={
            "user_id": user_id
        }
    )
    user = response.get("Item")
    if user is None:
        return {
            "statusCode": 404,
            "body": json.dumps({
                "error": "User not found"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    payload["user_id"] = user_id
    payload["password"] = bcrypt.hashpw(payload["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    payload["profile"] = user["profile"] 
    payload["email"] = user["email"]
    try:
        users.put_item(
            Item=payload,
            ConditionExpression="attribute_exists(user_id)"
        )
        return {
            "statusCode": 200,
            "body": json.dumps({
                "user_id": user_id
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    except Exception as e:
        print(e)
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Internal server error"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
