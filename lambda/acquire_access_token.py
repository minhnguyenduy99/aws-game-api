import json
import boto3
import jwt
import datetime
import os
from custom import (generate_access_token, parse_cookies)

db = boto3.resource("dynamodb")
USER_TABLE_NAME = os.environ.get("TABLE_NAME")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
users = db.Table(USER_TABLE_NAME)

def handler(event, context):
    cookies = parse_cookies(event["headers"]["Cookie"])
    refresh_token = cookies.get("refresh_token")
    if refresh_token is None:
        return {
            "statusCode": 403,
            "body": json.dumps({
                "error": "Unauthenticated user"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    error = None
    new_token = None
    try:
        payload = jwt.decode(refresh_token, JWT_SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]
        print(f"user_id: {user_id}")
        # Check if user exists
        response = users.get_item(
            Key={
                "user_id": user_id
            }
        )
        if response.get("Item") is None:
            raise Exception("User is invalid")
        new_token = generate_access_token(payload["user_id"], JWT_SECRET_KEY)
    except jwt.ExpiredSignatureError:
        error = "The token has been expired"
    except jwt.InvalidTokenError:
        error = "Invalid token"
    except:
        error = "Decoding error"
    finally: 
        if error:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": error
                }),
                "headers": {
                    "Access-Control-Allow-Origin": "*"
                }
            }
        return {
            "statusCode": 200,
            "body": json.dumps({
                "token": new_token
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }