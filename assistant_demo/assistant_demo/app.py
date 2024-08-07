import json

from dotenv import load_dotenv
from flask import Flask, request
from unique_toolkit.app import (
    EventName,
    Event,
    verify_signature_and_construct_event,
    init_logging,
    get_endpoint_secret,
    init_sdk,
)
from unique_toolkit.language_model import (
    LanguageModelService,
    LanguageModel,
    LanguageModelName,
    LanguageModelMessages,
    LanguageModelAssistantMessage,
    LanguageModelUserMessage,
)

load_dotenv()
init_sdk()
init_logging()

EXTERNAL_MODULE_NAME = "ASYNC_UNIQUE_ASSISTANT_APP"

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():
    event = None
    payload = request.data
    app.logger.info(f"{EXTERNAL_MODULE_NAME} - received webhook request")

    try:
        payload_decoded = json.loads(payload)
    except json.decoder.JSONDecodeError:
        return "Invalid payload", 400

    if payload_decoded["event"] != EventName.EXTERNAL_MODULE_CHOSEN:
        return "Not external module event", 400

    endpoint_secret = get_endpoint_secret()
    if endpoint_secret:
        # Only verify the event if there is an endpoint secret defined
        event = verify_signature_and_construct_event(
            headers=request.headers,
            payload=payload,
            endpoint_secret=endpoint_secret,
            logger=app.logger,
        )
        if isinstance(event, tuple):
            return event  # Error response
    else:
        try:
            event = Event(**payload_decoded)
        except ValueError as e:
            app.logger.error(f"Error deserializing event: {e}")
            return "Invalid event", 400

    # Verify the module name in the event received
    if event.payload.name != EXTERNAL_MODULE_NAME:
        return f"Not {EXTERNAL_MODULE_NAME} event", 400

    app.logger.info(f"{EXTERNAL_MODULE_NAME} event received.")

    # Initialize the language model service with the state
    language_model_service = LanguageModelService(event=event)
    language_model = LanguageModel(LanguageModelName.AZURE_GPT_35_TURBO)

    # stream the completion to the chat
    language_model_service.stream_complete(
        messages=LanguageModelMessages(
            [
                LanguageModelAssistantMessage(
                    content="You are Shakespeare and you tell short jokes."
                ),
                LanguageModelUserMessage(content="Tell me a joke."),
            ]
        ),
        model_name=language_model.name,
    )

    return "OK", 200
