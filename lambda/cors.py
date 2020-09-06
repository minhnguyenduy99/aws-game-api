import json

def handler(event, context):
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Headers": '*',
            "Access-Control-Allow-Origin": '*',
            "Access-Control-Allow-Methods": '*'
        }
    }