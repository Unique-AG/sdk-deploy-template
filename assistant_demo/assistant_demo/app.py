import json
import os
from http import HTTPStatus
from logging.config import dictConfig

import unique_sdk
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

unique_sdk.api_key = os.environ.get("API_KEY")
unique_sdk.app_id = os.environ.get("APP_ID")
if os.environ.get("API_BASE"):
    unique_sdk.api_base = os.environ.get("API_BASE")

assistant_id = os.environ.get("ASSISTANT_ID")
if os.environ.get("ENDPOINT_SECRET"):
    endpoint_secret = os.environ.get("ENDPOINT_SECRET")

dictConfig(
    {
        "version": 1,
        "root": {"level": "DEBUG", "handlers": ["console"]},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
            }
        },
    }
)

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello from the Assistant Demo! 🚀"


@app.route("/webhook", methods=["POST"])
def webhook():
    event = None
    payload = request.data

    app.logger.info("Received webhook request.")

    try:
        event = json.loads(payload)
    except json.decoder.JSONDecodeError:
        return "Invalid payload", 400

    if endpoint_secret:
        # Only verify the event if there is an endpoint secret defined
        # Otherwise use the basic event deserialized with json
        sig_header = request.headers.get("X-Unique-Signature")
        timestamp = request.headers.get("X-Unique-Created-At")

        if not sig_header or not timestamp:
            print("⚠️  Webhook signature or timestamp headers missing.")
            return jsonify(success=False), HTTPStatus.BAD_REQUEST

        try:
            event = unique_sdk.Webhook.construct_event(
                payload, sig_header, timestamp, endpoint_secret
            )
        except unique_sdk.SignatureVerificationError as e:
            print("⚠️  Webhook signature verification failed. " + str(e))
            return jsonify(success=False), HTTPStatus.BAD_REQUEST

    if (
        event
        and event["event"] == "unique.chat.user-message.created"
        and event["payload"]["assistantId"] == assistant_id
    ):
        message = event["payload"]["text"]
        app.logger.info(f"Received message: {message}")

        # Send a message back to the user
        unique_sdk.Message.create(
            user_id=event["userId"],
            company_id=event["companyId"],
            chatId=event["payload"]["chatId"],
            assistantId=assistant_id,
            text="Hello from the Assistant Demo! 🚀",
            role="ASSISTANT",
        )

    return "OK", 200
