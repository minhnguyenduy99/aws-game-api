import json
import boto3
import os
import uuid
import datetime
import jwt
import email
import base64
from custom import (
    parse_binary_multipart_to_form,
    validate_multipart_form_data
)

db = boto3.resource("dynamodb")
s3 = boto3.client("s3")
MAP_TABLE_NAME = os.environ.get("TABLE_NAME")
ROW_COUNT_TABLE_NAME = os.environ.get("ROW_COUNT_TABLE_NAME")
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
MAP_FOLDER = os.environ.get("S3_MAP_FOLDER")
game_maps = db.Table(MAP_TABLE_NAME)
row_count_table = db.Table(ROW_COUNT_TABLE_NAME)



required_keys = [
    "map_image",
    "map_file",
    "map_name"
]

def handler(event, context):
    form = parse_binary_multipart_to_form(event)
    if validate_multipart_form_data(form, required_keys) is False:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Invalid request body"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    user_id = event["requestContext"]["authorizer"]["user_id"]
    # Construct the payload before saving to database
    payload = construct_payload(form, user_id)

    try:
        map_image, map_file = (payload["map_image"], payload["map_file"])
        del payload["map_image"]
        del payload["map_file"]
        game_maps.put_item(
            Item=payload
        )
        s3.put_object(
            Bucket=BUCKET_NAME, 
            Key=MAP_FOLDER + "/" + map_image["file_name"], 
            Body=map_image["data"],
            ACL="public-read",
            ContentType="image/jpeg"
        )
        s3.put_object(
            Bucket=BUCKET_NAME, 
            Key=MAP_FOLDER + "/" + map_file["file_name"], 
            Body=map_file["data"],
            ACL="public-read",
            ContentType="application/json"
        )
        update_row_count()
        return {
            "statusCode": 201,
            "body": json.dumps({
                "message": "Create map successfully"
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


def update_row_count():
    response = row_count_table.get_item(
        Key={
            "table_name": MAP_TABLE_NAME
        }
    )
    table = response.get("Item")
    if table is None:
        raise Exception("Table name not found")
    count = table["row_count"] + 1
    item = {
        "table_name": MAP_TABLE_NAME,
        "row_count": count
    }
    try:
        row_count_table.put_item(
            Item=item
        )
    except Exception as e:
        print(f"Update table row count error: {e}")

def construct_payload(form, user_id):
    payload = get_payload_from_form(form)
    map_id = uuid.uuid4().hex[:10]
    payload["id"] = map_id
    payload["created_by"] = user_id
    payload["last_edited"] = str(datetime.datetime.now())
    payload["map_image"]["file_name"] = f"mapimage_{map_id}"
    payload["map_file"]["file_name"] = f"mapfile_{map_id}"
    return payload


def get_payload_from_form(form):
    if form is None:
        return None
    payload = {}
    for key in form:
        payload[key] = form[key]["value"]
    return payload


