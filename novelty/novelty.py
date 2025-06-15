import os
import requests
import chromadb
from chromadb.utils import embedding_functions

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
CHROMA_PATH = os.getenv('CHROMA_PATH', 'chroma')

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection('papers')

# OpenRouter embedding using text-embedding-ada

def _embed(text: str) -> list[float]:
    if not OPENROUTER_API_KEY:
        raise EnvironmentError('OPENROUTER_API_KEY not set')
    url = 'https://openrouter.ai/api/v1/embeddings'
    payload = {
        'model': 'text-embedding-ada-002',
        'input': text,
    }
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data['data'][0]['embedding']


def _crossref_hits(text: str) -> int:
    url = 'https://api.crossref.org/works'
    params = {
        'query.bibliographic': text,
        'rows': 1,
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get('message', {}).get('total-results', 0)


def assess(text: str) -> dict:
    """Assess novelty of given text."""
    embed = _embed(text)
    res = collection.query(query_embeddings=[embed], n_results=5)
    distances = res.get('distances', [[1]])[0]
    avg_dist = sum(distances) / len(distances) if distances else 1.0
    crossref = _crossref_hits(text)
    novel = avg_dist > 0.38 and crossref == 0
    score = avg_dist
    evidence = [f'avg_cosine_dist={avg_dist:.3f}', f'crossref_hits={crossref}']
    if novel:
        evidence.append('Novel by threshold')
    return {
        'score': float(score),
        'evidence': evidence,
    }
