import boto3
import os
import json
from custom import (RequestPaginator)

db = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME")
COUNT_ROW_TABLE_NAME = os.environ.get("ROW_COUNT_TABLE_NAME")
PAGE_SIZE = int(os.environ.get("PAGINATION_PAGE_SIZE"))
game_maps = db.Table(TABLE_NAME)
table_count = db.Table(COUNT_ROW_TABLE_NAME)

def handler(event, context):
    page = None
    try:
        page = int(event["queryStringParameters"]["page"])
    except ValueError:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "detail": "Invalid page"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    last_map_id = event["headers"]["amz-last-map-id"]
    if page <= 0:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "detail": "Invalid page"
            }),
            "headers": {
                "Access-Control-Allow-Origin": "*"
            }
        }
    user_id = event["requestContext"]["authorizer"]["user_id"]
    host = event["headers"]["Host"]
    path = event["requestContext"]["path"]
    url = f"https://{host}{path}"
    total_count = query_row_count()
    exclusive_start_key = get_exclusive_start_key(last_map_id)
    
    results = query(user_id, exclusive_start_key)
    if exclusive_start_key == None:
        page = 1

    paginator = RequestPaginator(
        request=url,
        total_result_count=total_count,
        page_size=PAGE_SIZE,
        param_name="page"
    )
    return {
        "statusCode": 200,
        "body": json.dumps(paginator.paginate(results, page)),
        "headers": {
            "Access-Control-Allow-Origin": "*"
        }
    }


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
    

def query(user_id, exclusive_start_key):
    if exclusive_start_key == None:
        response = game_maps.query(
            KeyConditionExpression="created_by = :u",
            ExpressionAttributeValues= {
                ":u": user_id
            },
            Limit=PAGE_SIZE
        )
    else:
        response = game_maps.query(
            KeyConditionExpression="created_by = :u",
            ExpressionAttributeValues= {
                ":u": user_id
            },
            Limit=PAGE_SIZE,
            ExclusiveStartKey=exclusive_start_key
        )
        
    results = response.get("Items")
    return results


def query_row_count():
    try:
        response = table_count.get_item(
            Key={
                "table_name": TABLE_NAME
            }
        )
        table = response["Item"]
        print(table)
        return int(str(table["row_count"]))
    except Exception as e:
        print(e)
        return 0

