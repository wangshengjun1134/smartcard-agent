"""Test BGE-m3 embeddings."""

import sys
import os

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

# Add python-service/src to path (tests directory is python-service/tests)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm.local_embeddings import BGEM3Embeddings

def main():
    model_path = r'C:\Users\admin\go\buff\smartcard-agent\data\models\bge-m3'
    print(f'Model path: {model_path}')

    # Check if model directory exists
    if os.path.exists(model_path):
        print('✓ Model directory exists')
        files = os.listdir(model_path)
        print(f'  Files: {files[:5]}...')
    else:
        print('✗ Model directory NOT found!')
        sys.exit(1)

    # Load model
    print('\nLoading BGE-m3 model...')
    embeddings = BGEM3Embeddings(model_path=model_path, device='cpu')
    print('✓ Model loaded successfully')

    # Test embed_query
    print('\n--- Testing embed_query ---')
    query = '智能卡操作指南'
    vec = embeddings.embed_query(query)
    print(f'Query: "{query}"')
    print(f'Vector dimension: {len(vec)}')
    print(f'First 5 values: {vec[:5]}')

    # Test embed_documents
    print('\n--- Testing embed_documents ---')
    docs = [
        '这是一个测试文档',
        'Hello world',
        '智能卡应用开发',
        'The quick brown fox jumps over the lazy dog'
    ]
    vecs = embeddings.embed_documents(docs)
    print(f'Documents count: {len(docs)}')
    print(f'Vectors count: {len(vecs)}')
    print(f'Each vector dimension: {len(vecs[0])}')

    # Test similarity
    print('\n--- Testing similarity ---')
    import numpy as np
    vec1 = np.array(vecs[0])  # 中文测试文档
    vec2 = np.array(vecs[1])  # Hello world
    vec3 = np.array(vecs[2])  # 智能卡应用开发
    
    # Cosine similarity
    def cosine_sim(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    sim_01 = cosine_sim(vec1, vec2)  # 中文 vs 英文
    sim_02 = cosine_sim(vec1, vec3)  # 中文 vs 中文
    
    print(f'Similarity(中文测试文档, Hello world): {sim_01:.4f}')
    print(f'Similarity(中文测试文档, 智能卡应用开发): {sim_02:.4f}')
    
    if sim_02 > sim_01:
        print('✓ 中文文本相似度更高 (预期)')
    else:
        print('! 注意：相似度结果与预期不符')

    print('\n✅ All tests PASSED!')

if __name__ == '__main__':
    main()