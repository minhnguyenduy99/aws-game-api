import json
import boto3
import os
import uuid

db = boto3.resource("dynamodb")
USER_TABLE_NAME = os.environ.get("TABLE_NAME")
users = db.Table(USER_TABLE_NAME)

def handler(event, context):
    user_id = event["pathParameters"]["user_id"]
    authenticted_user_id = event["requestContext"]["authorizer"]["user_id"]
    if user_id != authenticted_user_id:
        return {
            "statusCode": 401,
            "body": json.dumps({
                "error": "Unauthorized"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    # Check if the user with username exists
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
    del user["password"]
    return {
        "statusCode": 200,
        "body": json.dumps(user),
        "headers": {
            "Access-Control-Allow-Origin": "*"
        }
    }
