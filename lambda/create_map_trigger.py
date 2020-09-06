import json
import boto3
import datetime
import os


db = boto3.resource("dynamodb")
MAP_TABLE_NAME = os.environ.get("TABLE_NAME")
BUCKET_DOMAIN = os.environ.get("S3_BUCKET_DOMAIN")
game_maps = db.Table(MAP_TABLE_NAME)

def handler(event, context):
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    object_name = event["Records"][0]["s3"]["object"]["key"]
    file_url = f"{BUCKET_DOMAIN}/{bucket_name}/{object_name}"
    parts = object_name.split("_")
    file_type = parts[0].split("/")[1]
    map_id = parts[1]

    response = game_maps.query(
        IndexName="game-map-unique-map-id",
        KeyConditionExpression="id = :id",
        ExpressionAttributeValues={
            ":id": map_id
        }
    )
    if len(response.get("Items"))== 0:
        print("Error: map_id not found" + map_id)
        return
    
    game_map = response.get("Items")[0]
    field = None
    if file_type == "mapimage":
        field = "map_image_url"
    else:
        field = "map_file_url"
    try:
        response = game_maps.update_item(
            Key={
                "created_by": game_map["created_by"],
                "last_edited": game_map["last_edited"]
            },
            UpdateExpression="SET #url=:value",
            ExpressionAttributeNames={
                "#url": field
            },
            ExpressionAttributeValues={
                ":value": file_url
            }
        )
    except Exception as e: 
        print(e)

