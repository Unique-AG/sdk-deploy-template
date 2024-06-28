import json
import logging
import os
import unique_sdk

from dotenv import load_dotenv
from sseclient import SSEClient

# For more details about Event Socket and how to use it, please refer to the following link:
# https://unique-ch.atlassian.net/wiki/spaces/PUB/pages/631406621/Event+Socket+Streaming+Endpoint+SSE+-+Webhooks+Drop-In

# Module and subscription constants
MODULE_NAME = "AssistantDemo"
SUBSCRIPTIONS = "unique.chat.user-message.created"

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv("./.env", override=True)

unique_sdk.api_key = os.environ.get("API_KEY")
unique_sdk.app_id = os.environ.get("APP_ID")


def _get_sse_client():
    return SSEClient(
        url=f'{os.getenv("BASE_URL")}/public/event-socket/events/stream?subscriptions={SUBSCRIPTIONS}',
        headers={
            "Authorization": f'Bearer {os.getenv("API_KEY")}',
            "x-app-id": os.getenv("APP_ID"),
            "x-company-id": os.getenv("COMPANY_ID"),
        },
    )


def _process_event(event_data):
    try:
        event = json.loads(event_data)
        print(event)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
        return

    if (
        event
        and event["event"] in SUBSCRIPTIONS.split(",")
        and event["payload"]["assistantId"] == os.getenv("ASSISTANT_ID")
    ):
        logger.info(f"Event subscription received: {SUBSCRIPTIONS}")

        # Send a message back to the user
        unique_sdk.Message.create(
            user_id=event["userId"],
            company_id=event["companyId"],
            chatId=event["payload"]["chatId"],
            assistantId=os.getenv("ASSISTANT_ID"),
            text="Hello from the Assistant Demo! 🚀",
            role="ASSISTANT",
        )


def _event_socket():
    for event in _get_sse_client():
        logger.debug("New event received.")
        if not event.data:
            logger.warning("Received an empty message.")
            continue
        else:
            _process_event(event.data)


if __name__ == "__main__":
    _event_socket()
