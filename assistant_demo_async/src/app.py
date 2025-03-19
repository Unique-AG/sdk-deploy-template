import json

from dotenv import load_dotenv
from quart import Quart, request
from unique_toolkit.app import (
    EventName,
    ChatEvent,
    verify_signature_and_construct_event,
    init_logging,
    get_endpoint_secret,
    init_sdk,
)
from unique_toolkit.language_model import (
    LanguageModelService,
    LanguageModelName,
    LanguageModelMessages,
    Prompt,
)
from unique_toolkit.chat import ChatService
from unique_toolkit.language_model.infos import LanguageModelInfo

load_dotenv()
init_sdk()
init_logging()

MODULE_NAME = "ASYNC_UNIQUE_ASSISTANT_APP"

app = Quart(__name__)


@app.route("/webhook", methods=["POST"])
async def webhook():
    event = None
    payload = await request.data
    app.logger.info(f"{MODULE_NAME} - received webhook request")

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
            event = ChatEvent(**payload_decoded)
        except ValueError as e:
            app.logger.error(f"Error deserializing event: {e}")
            return "Invalid event", 400

    app.logger.info(f"Event: {event.model_dump()}")

    # Verify the module name in the event received
    if event.payload.name != MODULE_NAME:
        app.logger.error(f"Not {MODULE_NAME} event")
        return f"Not {MODULE_NAME} event", 400

    app.logger.info(f"{MODULE_NAME} event received.")

    try:
        # Initialize the language model service with the event
        language_model_service = LanguageModelService(event=event)
        language_model = LanguageModelInfo.from_name(
            LanguageModelName.AZURE_GPT_4_TURBO_2024_0409
        )
        chat_service = ChatService(event=event)

        system_prompt = Prompt(
            """You are a professional financial advisor specializing in ${financial_product}. 
            Your responses should be concise, data-driven, and focused on helping clients make informed investment decisions.
            Always consider risk management in your advice.""",
            financial_product="ETF",
        )

        user_prompt = Prompt(event.payload.user_message.text)

        # stream the completion to the chat
        result = await language_model_service.complete_async(
            messages=LanguageModelMessages(
                [
                    system_prompt.to_system_msg(),
                    user_prompt.to_user_msg(),
                ]
            ),
            model_name=language_model.name,
        )

        content = result.choices[0].message.content or "No response from model"
        if isinstance(content, list):
            content = json.dumps(content)

        await chat_service.create_assistant_message_async(content)

    except Exception as e:
        app.logger.error(f"Error processing event: {e}")
        return "Error processing event", 500

    return "OK", 200
