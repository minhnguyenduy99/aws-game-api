import boto3
import os
import json
import datetime

db = boto3.resource("dynamodb")
GAMEMAP_TABLE_NAME = os.environ.get("GAMEMAP_TABLE_NAME")
GAMESTATE_TABLE_NAME = os.environ.get("GAMESTATE_TABLE_NAME")
game_maps = db.Table(GAMEMAP_TABLE_NAME)
game_states = db.Table(GAMESTATE_TABLE_NAME)
STATE_VALUES = ["NA", "AR", "OP"]

def handler(event, context):
    query = event["queryStringParameters"]
    map_id, state = (query["map_id"], query["state"])
    user_id = event["requestContext"]["authorizer"]["user_id"]
    
    # State is invalid
    if state not in STATE_VALUES:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": f"state '{state}' is invalid"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    map_not_found = get_map_not_found_response(map_id)
    # Map is not found
    if map_not_found is not None:
        return map_not_found

    game_state = create_gamestate(user_id, map_id, state)
    return {
        "statusCode": 201,
        "body": json.dumps(game_state),
        "headers": {
            "Access-Control-Allow-Origin": "*"
        }
    }


def get_map_not_found_response(map_id):
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
            })
        }
    return None


def get_gamestate(user_id, map_id):
    response = game_states.get_item(
        Key={
            "user_id": user_id,
            "map_id": map_id
        }
    )
    return response.get("Item")

def create_gamestate(user_id, map_id, state):
    response = game_states.get_item(
        Key={
            "user": user_id,
            "game_map": map_id
        }
    )
    game_state = response.get("Item")
    if game_state is not None:
        game_state["state"] = state
        game_state["saved_date"] = str(datetime.datetime.now())
        game_states.put_item(
            Item=game_state
        )
        return game_state
    game_state = {
        "user": user_id,
        "game_map": map_id,
        "state": state,
        "saved_date": str(datetime.datetime.now())
    }
    game_states.put_item(
        Item = game_state
    )
    return game_state


    


