import json

def handler(event, context):
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'status': 'healthy',
            'message': 'SHL Assessment Recommender API is running',
            'endpoints': {
                'GET /.netlify/functions/health': 'Health check',
                'POST /.netlify/functions/recommend': 'Get recommendations'
            }
        })
    }