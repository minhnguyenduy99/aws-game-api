import json
import boto3
import jwt

def handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': jwt.encode({ 'hello': 'aba' }, 'key', 'SHA256')
        })
    }
