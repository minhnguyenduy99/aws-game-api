import json
import boto3
import os

db = boto3.resource("dynamodb")
MAP_TABLE_NAME = os.environ.get("TABLE_NAME")
game_maps = db.Table(MAP_TABLE_NAME)

def handler(event, context):
    map_id = event["pathParameters"]["id"]
    user_id = event["requestContext"]["authorizer"]["user_id"]

    response = game_maps.query(
        IndexName="game-map-unique-map-id",
        KeyConditionExpression="id=:mi",
        ExpressionAttributeValues={
            ":mi": map_id
        }
    )
    if len(response.get("Items")) == 0:
        return {
            "statusCode": 404,
            "body": json.dumps({
                "error": "Map not found"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    game_map = response.get("Items")[0]
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
    return {
        "statusCode": 200,
        "body": json.dumps(game_map),
        "headers": {
            "Access-Control-Allow-Origin": "*"
        }
    }
