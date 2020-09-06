import json
import boto3
import bcrypt
import os
from custom import (generate_access_token, generate_refresh_token)

db = boto3.resource("dynamodb")
USER_TABLE_NAME = os.environ.get("TABLE_NAME")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
users = db.Table(USER_TABLE_NAME)

def handler(event, context):
    print(event["body"])
    payload = json.loads(event["body"])
    response = users.query(
        IndexName="user-unique-username-project-all",
        KeyConditionExpression="username = :un",
        ExpressionAttributeValues={
            ":un": payload["username"]
        }
    )
    if len(response.get("Items")) == 0:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Username or password is incorrect"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    user = response.get("Items")[0]
    if check_password(user, payload["password"]) is False:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Username or password is incorrect"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    access_token = generate_access_token(user["user_id"], JWT_SECRET_KEY)
    refresh_token = generate_refresh_token(user["user_id"], JWT_SECRET_KEY)
    del user["password"]
    return {
        "statusCode": 200,
        "headers": {
            "Set-Cookie": f"refresh_token={refresh_token};HttpOnly",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True
        },
        "body": json.dumps({
            "access_token": access_token,
            "user": user
        })
    }


def check_password(user, password_text):
    password_correct = bcrypt.checkpw(password_text.encode("utf-8"), user["password"].encode("utf-8"))
    return password_correct
