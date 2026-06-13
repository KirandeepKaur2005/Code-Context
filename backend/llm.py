from ollama import chat
import time
import requests

MODEL_NAME = "qwen2.5-coder:3b"
def warmup_model():
    try:
        requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": "",
                "keep_alive": "1h"
            },
            timeout=60
        )

        print("Model warmed up for 1 hour")

    except Exception as e:
        print("Error warming up model:")
        print(e)

def unload_model():
    try:
        requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": MODEL_NAME,
                "keep_alive": 0
            }
        )

        print("Model unloaded")

    except Exception as e:
        print("Failed to unload model")
        print(e)

def generate_response(question, context):
    SYSTEM_PROMPT = """/no_think
    You are a senior software engineer helping a developer understand a repository.

    Rules:
    - Answer ONLY from the provided code chunks.
    - Use clear, developer-friendly language.
    - Describe the flow when relevant.
    - Answer ONLY from the provided code chunks
    - If information is missing, say "Not found in the indexed code."

    If the user asks for code:
    1. Show relevant code snippets from the provided context.
    2. Quote exact code.
    3. Explain the code afterward.
    4. If the code is incomplete in the provided context, say:
    'Implementation is partially visible in the indexed chunks.'
    """

    USER_PROMPT = f"""
    Repository code chunks:

    {context}

    Question:
    {question}

    Respond in the following format:

    Answer:
    - Be brief and concise with answers
    - List relevant files
    - Mention important functions/classes
    - Mention the flow if relevant

    If the answer is not present in the code, say:
    "Not found in the indexed code."
    """
    
    start_time = time.time()

    try:
        response = chat(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": USER_PROMPT
                }
            ],
            options={
                "temperature": 0.3,
                "num_ctx": 4096
            }
        )
    except Exception as e:
        print(" --- Error generated in llm.py during response generation")
        print(e)


    end_time = time.time()
    print("Time taken to generate response: ", end_time-start_time)
    
    print("response: ", response)
    return response["message"]["content"]