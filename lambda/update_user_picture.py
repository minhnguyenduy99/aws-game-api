import json
import boto3
import datetime
import os


db = boto3.resource("dynamodb")
USER_TABLE_NAME = os.environ.get("TABLE_NAME")
BUCKET_DOMAIN = os.environ.get("S3_BUCKET_DOMAIN")
users = db.Table(USER_TABLE_NAME)

def handler(event, context):
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    object_name = event["Records"][0]["s3"]["object"]["key"]
    file_url = f"{BUCKET_DOMAIN}/{bucket_name}/{object_name}"
    user_id = object_name.split("_")[1].split(".")[0]

    response = users.get_item(
        Key={
            "user_id": user_id
        }
    )
    if response.get("Item") is None:
        print("Error: user_id not found" + user_id)
        return
    
    user = response.get("Item")
    user["profile"]["picture"] = file_url
    
    try:
        response = users.put_item(
            Item=user,
            ConditionExpression="attribute_exists(user_id)"
        )
    except Exception as e: 
        print(e)

