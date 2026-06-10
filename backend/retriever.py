from embedder import get_embedding
from database import search_vectors
import time

def retrieve(repo_name, query, top_k=5):
    start_time = time.time()
    query_embedding = get_embedding(query)
    end_time = time.time()
    print("Time taken to generate query_embedding: ", end_time-start_time)

    start_time = time.time()
    results = search_vectors(query_embedding, repo_name, top_k)
    end_time = time.time()
    print("Time taken to search vectors: ", end_time-start_time)

    return results