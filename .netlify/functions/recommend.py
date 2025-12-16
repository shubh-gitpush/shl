import json
import os
import sys

# Add the project root to the path
sys.path.append('/opt/buildhome/repo')

def handler(event, context):
    # Handle CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}
    
    try:
        # Import here to avoid issues during cold start
        import numpy as np
        import pandas as pd
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        import requests
        from bs4 import BeautifulSoup
        
        # Load assessments data
        data_path = '/opt/buildhome/repo/assessments_all.json'
        if not os.path.exists(data_path):
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': f'Data file not found at {data_path}'})
            }
            
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Process records
        records = []
        for item in data:
            name = item.get("name", "").strip()
            if "solution" in name.lower():
                continue
            url = item.get("url", "").strip()
            desc = item.get("description", "").strip()
            if name and url and desc:
                records.append({
                    "name": name,
                    "url": url,
                    "text": f"{name}. {desc}"
                })
        
        if event.get('httpMethod') == 'GET':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    'message': 'SHL Assessment Recommender API',
                    'status': 'ready',
                    'assessments_loaded': len(records)
                })
            }
        
        # Handle POST request
        if event.get('httpMethod') != 'POST':
            return {
                'statusCode': 405,
                'headers': headers,
                'body': json.dumps({'error': 'Method not allowed'})
            }
        
        body = json.loads(event.get('body', '{}'))
        query_text = body.get('query')
        
        if not query_text:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Query parameter required'})
            }
        
        # Initialize model and get recommendations
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Encode texts
        assessment_texts = [r["text"] for r in records]
        embeddings = model.encode(assessment_texts)
        query_emb = model.encode([query_text])
        
        # Calculate similarity
        scores = cosine_similarity(query_emb, embeddings)[0]
        top_idx = np.argsort(scores)[-10:][::-1]
        
        results = []
        for i in top_idx:
            results.append({
                "Assessment name": records[i]["name"],
                "URL": records[i]["url"],
                "score": float(scores[i])
            })
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'query': query_text,
                'results': results[:10]
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': str(e),
                'type': 'internal_error'
            })
        }