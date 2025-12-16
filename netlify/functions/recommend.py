import json
import os

def main(event, context):
    """
    Netlify Function handler for SHL Assessment Recommender
    """
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': ''
            }
        
        # Handle GET request for health check
        if event.get('httpMethod') == 'GET':
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'message': 'SHL Assessment Recommender API is running',
                    'endpoints': {
                        'POST /api/recommend': 'Get recommendations with query or url'
                    }
                })
            }
        
        # Parse the request body
        if event.get('httpMethod') != 'POST':
            return {
                'statusCode': 405,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        body = json.loads(event.get('body', '{}'))
        
        # For now, return a simple mock response
        body = json.loads(event.get('body', '{}'))
        
        query = body.get('query', 'test query')
        
        # Mock recommendations
        mock_results = [
            {
                'Assessment name': 'Numerical Reasoning Test',
                'URL': 'https://www.shl.com/assessments/numerical-reasoning/'
            },
            {
                'Assessment name': 'Verbal Reasoning Test', 
                'URL': 'https://www.shl.com/assessments/verbal-reasoning/'
            },
            {
                'Assessment name': 'Logical Reasoning Test',
                'URL': 'https://www.shl.com/assessments/logical-reasoning/'
            }
        ]
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'query': query,
                'results': mock_results,
                'note': 'This is a mock response. Full ML model coming soon!'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }

# Also alias as handler for compatibility
handler = main