from flask import Flask, request, jsonify
from flask_cors import CORS
from threading import Thread
import atexit

from rag import ask
from pipeline import index_repository
from file_watchdog import start_watching
from llm import warmup_model, unload_model

app = Flask(__name__)
CORS(app)

ACTIVE_WATCHERS = set()

warmup_model()
atexit.register(unload_model)

@app.route("/query", methods=["POST"])
def query():

    data = request.json

    repo_name = data.get("repo_name")
    question = data.get("question")

    if not repo_name or not question:
        return jsonify({
            "error": "repo_name and question are required"
        }), 400

    answer = ask(repo_name, question)

    return jsonify({
        "answer": answer
    })

@app.route("/index", methods=["POST"])
def index_repo():

    data = request.json

    repo_path = data.get("repo_path")

    if not repo_path:
        return jsonify({
            "error": "repo_path required"
        }), 400

    index_repository(repo_path)

    if repo_path not in ACTIVE_WATCHERS:

        Thread(
            target=start_watching,
            args=(repo_path,),
            daemon=True
        ).start()

        ACTIVE_WATCHERS.add(repo_path)

    return jsonify({
        "message": "Repository indexed successfully"
    })


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        use_reloader=False
    )