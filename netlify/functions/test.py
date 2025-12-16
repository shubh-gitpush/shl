import json

def main(event, context):
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'message': 'Test function is working!',
            'method': event.get('httpMethod', 'UNKNOWN'),
            'path': event.get('path', 'UNKNOWN')
        })
    }

# Alias for compatibility
handler = main