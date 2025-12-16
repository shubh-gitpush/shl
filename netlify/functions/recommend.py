import json
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shl_recommender import recommend, extract_text_from_url

def handler(event, context):
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
        
        # Parse the request body
        if event.get('httpMethod') != 'POST':
            return {
                'statusCode': 405,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        body = json.loads(event.get('body', '{}'))
        
        # Extract query or URL
        query_text = None
        if body.get('url'):
            text = extract_text_from_url(body['url'])
            if not text:
                return {
                    'statusCode': 400,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Unable to extract text from URL'})
                }
            query_text = text
        elif body.get('query'):
            query_text = body['query']
        else:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Provide either query or url'})
            }
        
        # Get recommendations
        results = recommend(query_text, k=10)
        
        # Return results
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'results': [
                    {'Assessment name': r['assessment_name'], 'URL': r['url']}
                    for r in results
                ]
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }