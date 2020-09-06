import boto3
import os
import json
import datetime
from custom import (RequestPaginator)

db = boto3.resource("dynamodb")
GAMEMAP_TABLE_NAME = os.environ.get("GAMEMAP_TABLE_NAME")
GAMESTATE_TABLE_NAME = os.environ.get("GAMESTATE_TABLE_NAME")
ROW_COUNT_TABLE_NAME = os.environ.get("ROW_COUNT_TABLE_NAME")
PAGE_SIZE = int(os.environ.get("PAGINATION_PAGE_SIZE"))
game_maps = db.Table(GAMEMAP_TABLE_NAME)
game_states = db.Table(GAMESTATE_TABLE_NAME)
row_count_table = db.Table(ROW_COUNT_TABLE_NAME)

def handler(event, context):
    # Validate page value
    page = get_page(event)
    if page is None:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "detail": "Invalid page"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }

    # Retrieve all needed values
    host = event["headers"]["Host"]
    path = event["requestContext"]["path"]
    url = f"https://{host}{path}"
    last_map_id = event["headers"]["amz-last-map-id"]
    user_id = event["requestContext"]["authorizer"]["user_id"]
    exclusive_start_key = get_exclusive_start_key(last_map_id)

    # construct list of game states
    list_maps = query_map(exclusive_start_key)
    list_gamestates = query_gamestate(user_id, list_maps)
    gamestates_map_ids = set([game_map_id for game_map_id in list_gamestates.keys()])
    for map_id in list_maps:
        if map_id not in gamestates_map_ids:
            list_gamestates[map_id] = create_gamestate(user_id, list_maps[map_id]) 
        else:
            list_gamestates[map_id]["game_map"] = list_maps[map_id]
    
    total_count = int(str(get_gamestate_count()))
    paginator = RequestPaginator(
        request=url,
        total_result_count=total_count,
        page_size=PAGE_SIZE,
        param_name="page"
    )
    return {
        "statusCode": 200,
        "body": json.dumps(paginator.paginate(list(list_gamestates.values()), page)),
        "headers": {
            "Access-Control-Allow-Origin": "*"
        }
    }


def create_gamestate(user_id, game_map):
    return {
        "user": user_id,
        "saved_date": str(datetime.datetime.now()),
        "state": "NA",
        "game_map": game_map
    }


def get_page(event):
    try:
        page = int(event["queryStringParameters"]["page"])
        if page <= 0:
            return None
        return page
    except ValueError:
        return None


def get_exclusive_start_key(map_id):
    response = game_maps.query(
        IndexName="game-map-unique-map-id",
        KeyConditionExpression="id = :mi",
        ExpressionAttributeValues={
            ":mi": map_id
        }
    )
    if len(response.get("Items")) == 0:
        return None
    item = response.get("Items")[0]
    return {
        "created_by": item["created_by"],
        "last_edited": item["last_edited"]
    }
    

def query_map(exclusive_start_key) -> dict:
    if exclusive_start_key == None:
        response = game_maps.scan(
            Limit=PAGE_SIZE
        )
    else:
        response = game_maps.scan(
            Limit=PAGE_SIZE,
            ExclusiveStartKey=exclusive_start_key
        )

    results = response.get("Items")
    map_results = {}    
    for result in results:
        map_results[result["id"]] = result

    return map_results


def query_gamestate(user_id, dict_gamemap: dict) -> dict:
    list_map_ids = [map_id for map_id in dict_gamemap]
    print(list_map_ids)
    list_gamestates = {}
    for map_id in list_map_ids:
        response = game_states.get_item(
            Key={
                "user": user_id,
                "game_map": map_id
            }
        )
        game_state = response.get("Item")
        if game_state is not None:
            list_gamestates[map_id] = game_state
    return list_gamestates


def get_gamestate_count() -> int:
    response = row_count_table.get_item(
        Key={
            "table_name": GAMEMAP_TABLE_NAME
        }
    )
    return response.get("Item")["row_count"]
