from sentence_transformers import SentenceTransformer

# Load model from hugging face
# model = SentenceTransformer(
#     "BAAI/bge-small-en-v1.5"
# )

model = SentenceTransformer(
    "C:/Users/ASUS/.cache/huggingface/hub/models--BAAI--bge-small-en-v1.5/snapshots/5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
)

def get_embedding(text):
    return model.encode(text).tolist()