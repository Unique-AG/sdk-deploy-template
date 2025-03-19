from dotenv import load_dotenv
from flask import Flask, request
from unique_toolkit.app import (
    Event,
    init_logging,
    init_sdk,
)
from unique_toolkit.app.verification import verify_request_and_construct_event
from unique_toolkit.chat import ChatService
from unique_toolkit.language_model import (
    LanguageModelService,
    LanguageModelName,
    LanguageModelMessages,
    Prompt,
)

load_dotenv()
init_sdk()
init_logging()

MODULE_NAME = "SYNC_UNIQUE_ASSISTANT_APP"

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():
    app.logger.info(f"{MODULE_NAME} - received webhook request")
    event, status_code = verify_request_and_construct_event(
        assistant_name=MODULE_NAME,
        payload=request.data,
        headers=dict(request.headers),
        event_constructor=Event,
    )

    if isinstance(event, str):
        return event, status_code

    try:
        # Initialize the language model service with the state
        language_model_service = LanguageModelService(event=event)
        chat_service = ChatService(event=event)
        chat_service.modify_assistant_message(content="Generating response...")

        system_prompt = Prompt(
            """You are a professional financial advisor specializing in ${financial_product}. 
            Your responses should be concise, data-driven, and focused on helping clients make informed investment decisions.
            Always consider risk management in your advice.""",
            financial_product="ETF",
        )
        user_prompt = Prompt(event.payload.user_message.text)

        messages = LanguageModelMessages(
            [
                system_prompt.to_system_msg(),
                user_prompt.to_user_msg(),
            ]
        )

        # Complete the response
        result = language_model_service.complete(
            messages=messages,
            model_name=LanguageModelName.AZURE_GPT_4_TURBO_2024_0409,
        )

        # Modify the assistant message with the response
        content = result.choices[0].message.content
        if isinstance(content, str):
            chat_service.modify_assistant_message(content=content)

        # OR
        # Stream the response directly to the chat
        # chat_service.stream_complete(
        #     messages=messages,
        #     model_name=language_model.name,
        # )

        # Inform the UI that the response is complete
        chat_service.modify_assistant_message(set_completed_at=True)

    except Exception as e:
        app.logger.error(f"Error processing event: {e}")
        return "Error processing event", 500

    return "OK", status_code
