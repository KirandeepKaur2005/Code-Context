from parser import process_repository
from embedder import get_embedding
from database import store_chunks

def index_repository(repo_path):
    chunks = process_repository(repo_path)

    rows = []

    for chunk in chunks:
        content = chunk["content"]
        print(content)

        try:
            embedding = get_embedding(content)
            print("Embeddings generated")
        except Exception as e:
            print("---Error in pipeline.py while generating embeddings: ", e)

        rows.append((
            chunk["repo_name"],
            chunk["file_path"],
            chunk["language"],
            chunk["start_line"],
            chunk["end_line"],
            chunk["content"],
            embedding
        ))

    try:
        store_chunks(rows)
        print("Embeddings stored")
    except Exception as e:
        print(" --- Error in pipeline.py while storing chunks: ")
        print(e)

    print(f"Indexed {len(chunks)} chunks")

if __name__ == "__main__":
    index_repository("../../Devsearch")