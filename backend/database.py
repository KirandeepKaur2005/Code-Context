import os
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()

DB_PARAMS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": "localhost",
    "port": "5433"
}

def get_connection():
    return psycopg2.connect(**DB_PARAMS)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
            CREATE EXTENSION IF NOT EXISTS vector;
        """
    )

    cur.execute(
        """
            CREATE TABLE IF NOT EXISTS codebase_vectors(
                id SERIAL PRIMARY KEY,
                repo_name TEXT,
                file_path TEXT,
                language TEXT,
                start_line INT,
                end_line INT,
                content TEXT,
                embedding vector(384)
            );
        """
    )

    conn.commit()

    cur.close()
    conn.close()

    print("Database table codebase_vectors initialized")

def store_chunks(rows):
    conn = get_connection()
    cur = conn.cursor()

    # optimized query for inserting values
    execute_values(
        cur, 
        """
            INSERT INTO codebase_vectors (
                repo_name,
                file_path,
                language,
                start_line,
                end_line,
                content,
                embedding
            )
            VALUES %s;
        """,
        rows
    )

    conn.commit()

    cur.close()
    conn.close()

def search_vectors(query_embedding, repo_name, limit=5):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
            SELECT 
                repo_name,
                file_path,
                language,
                start_line,
                end_line,
                content,
                embedding <=> %s::vector AS distance
            FROM codebase_vectors
            WHERE repo_name = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, 
        (
            query_embedding,
            repo_name,
            query_embedding,
            limit
        )
    )

    results = cur.fetchall()

    cur.close()
    conn.close()

    return results

def clear_file_vectors(file_path):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
            DELETE FROM codebase_vectors 
            WHERE file_path = %s;
        """, 
        (file_path,) # need a tuple here
    )

    conn.commit()

    cur.close()
    conn.close()

def clear_repository(repo_name):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
            DELETE FROM codebase_vectors
            WHERE repo_name = %s
        """,
        (repo_name,)
    )

    conn.commit()

    cur.close()
    conn.close()

def get_already_indexed_repos():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
            SELECT DISTINCT repo_name
            FROM codebase_vectors;
        """
    )

    results = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return results

if __name__ == "__main__":
    init_db()