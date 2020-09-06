import json
import boto3
import os
import datetime
from custom import (
    parse_binary_multipart_to_form,
    validate_multipart_form_data
)

db = boto3.resource("dynamodb")
s3 = boto3.client("s3")
MAP_TABLE_NAME = os.environ.get("TABLE_NAME")
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
MAP_FOLDER = os.environ.get("S3_MAP_FOLDER")
game_maps = db.Table(MAP_TABLE_NAME)



required_keys = [
    "map_image",
    "map_file",
    "map_name"
]

def handler(event, context):
    form = parse_binary_multipart_to_form(event)
    user_id = event["requestContext"]["authorizer"]["user_id"]

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
    [game_map, not_found_response] = get_map_or_not_found(event["pathParameters"]["id"])
    if not_found_response:
        return not_found_response

    if user_id != game_map["created_by"]:
        return {
            "statusCode": 401,
            "body": json.dumps({
                "error": "Unauthorized"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    # Construct the payload before saving to database
    payload = construct_payload(form, game_map)

    try:
        map_image, map_file = (payload["map_image"], payload["map_file"])
        del payload["map_image"]
        del payload["map_file"]
        print(game_map)
        game_maps.delete_item(
            Key={
                "created_by": game_map["created_by"],
                "last_edited": game_map["last_edited"]
            }
        )
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
        return {
            "statusCode": 200,
            "body": json.dumps({
                "map_id": game_map["id"]
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

def construct_payload(form, old_map):
    payload = get_payload_from_form(form)
    map_id = old_map["id"]
    payload["id"] = old_map["id"]
    payload["created_by"] = old_map["created_by"]
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


def get_map_or_not_found(map_id):
    response = game_maps.query(
        IndexName="game-map-unique-map-id",
        KeyConditionExpression="id=:mi",
        ExpressionAttributeValues={
            ":mi": map_id
        }
    )
    if len(response.get("Items")) == 0:
        return [
            None,
            {
                "statusCode": 404,
                "body": json.dumps({
                    "error": "Map not found"
                })
            }
        ]
    return [
        response.get("Items")[0],
        None
    ]