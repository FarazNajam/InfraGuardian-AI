from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

TEST_AGENT_URL = os.environ.get(
    "TEST_AGENT_URL",
    "http://localhost:8000"
)


@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "healthy",
        "application": "infraguardian-api"
    })


@app.route("/api/test", methods=["POST"])
def run_test():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "JSON body required"
        }), 400

    application_url = data.get("application_url")
    instructions = data.get("instructions")

    if not application_url:
        return jsonify({
            "error": "application_url is required"
        }), 400

    if not instructions:
        return jsonify({
            "error": "instructions are required"
        }), 400

    payload = {
        "application_url": application_url,
        "instructions": instructions
    }

    try:

        response = requests.post(
            f"{TEST_AGENT_URL}/test",
            json=payload,
            timeout=600
        )

        response.raise_for_status()

        return jsonify(response.json())

    except requests.RequestException as error:

        return jsonify({
            "error": "Unable to reach Test Agent",
            "details": str(error)
        }), 502


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5001)),
        debug=True
    )