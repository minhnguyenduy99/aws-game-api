import json
import boto3
import os

db = boto3.resource("dynamodb")
MAP_TABLE_NAME = os.environ.get("GAMEMAP_TABLE_NAME")
GAMESTATE_TABLE_NAME = os.environ.get("GAMESTATE_TABLE_NAME")
game_maps = db.Table(MAP_TABLE_NAME)
game_states = db.Table(GAMESTATE_TABLE_NAME)

def handler(event, context):
    map_id = event["pathParameters"]["map_id"]
    user_id = event["requestContext"]["authorizer"]["user_id"]
    game_map = get_gamemap(map_id)
    game_state = get_gamestate(user_id, map_id)
    
    if game_map is None:
        return {
            "statusCode": 404,
            "body": json.dumps({
                "error": "Map not found"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    game_state["game_map"] = game_map
    return {
        "statusCode": 200,
        "body": json.dumps(game_state),
        "headers": {
            "Access-Control-Allow-Origin": "*"
        }
    }


def get_gamemap(map_id):
    response = game_maps.query(
        IndexName="game-map-unique-map-id",
        KeyConditionExpression="id=:mi",
        ExpressionAttributeValues={
            ":mi": map_id
        }
    )
    if len(response.get("Items")) == 0:
        return None
    return response.get("Items")[0]


def get_gamestate(user_id, map_id):
    response = game_states.get_item(
        Key={
            "user": user_id,
            "game_map": map_id
        }
    )
    game_state = response.get("Item")
    if game_state is not None:
        return game_state
    game_state = {
        "user": user_id,
        "game_map": map_id, 
        "state": "NA",
        "saved_date": None
    }
    return game_state

    
