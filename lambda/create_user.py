import json
import boto3
import os
import uuid
import bcrypt
import datetime
import jwt
import email
import base64
from custom import (
    generate_access_token, 
    parse_binary_multipart_to_form
)

db = boto3.resource("dynamodb")
s3 = boto3.client("s3")
USER_TABLE_NAME = os.environ.get("TABLE_NAME")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
FOLDER_NAME = os.environ.get("S3_USER_FOLDER_NAME")
users = db.Table(USER_TABLE_NAME)



required_keys = [
    "username",
    "password",
    "email",
    "given_name",
    "family_name"
]

def handler(event, context):
    form = parse_binary_multipart_to_form(event)
    are_keys_represented = all(form.get(key) is not None for key in required_keys)
    if are_keys_represented is False:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Invalid request body"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    # Check if the user with given username exists
    user_exists = get_user_exists_response(form["username"]["value"])
    if user_exists is not None:
        return user_exists
    # Construct the payload before saving to database
    payload = construct_payload(form)
    try:
        picture = payload["picture"]
        del payload["picture"]
        users.put_item(
            Item=payload
        )
        s3.put_object(
            Bucket=BUCKET_NAME, 
            Key=FOLDER_NAME + "/" + picture["file_name"], 
            Body=picture["data"], 
            ACL="public-read",
            ContentType="image/jpeg"
        )
        payload["access_token"] = generate_access_token(payload["user_id"], JWT_SECRET_KEY)
        del payload["password"]
        return {
            "statusCode": 201,
            "body": json.dumps(payload),
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


def get_user_exists_response(username):
    response = users.query(
        IndexName="user-unique-username-project-all",
        KeyConditionExpression="username = :un",
        ExpressionAttributeValues={
            ":un": username
        }
    )
    if len(response["Items"]) > 0:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "The username exists"   
            })
        }
    return None

def construct_payload(form):
    payload = get_payload_from_form(form)
    user_id = uuid.uuid4().hex[:10]
    payload["user_id"] = user_id
    payload["password"] = str(bcrypt.hashpw(payload["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8"))
    picture_ext = form["picture"]["file_name"].split(".")[-1]
    if not picture_ext:
        picture_ext = ""
    file_name = f"user_{user_id}.{picture_ext}"
    payload["picture"]["file_name"] = file_name
    profile_keys = ["given_name", "family_name"]
    payload["profile"] = {}
    for key in payload:
        if key in profile_keys:
            payload["profile"][key] = payload.get(key)
    for key in profile_keys:
        payload.pop(key)
    return payload


def get_payload_from_form(form):
    if form is None:
        return None
    payload = {}
    for key in form:
        payload[key] = form[key]["value"]
    return payload
