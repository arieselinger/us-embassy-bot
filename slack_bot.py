import logging
import json

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)
client = WebClient()


def connect_client(token):
    global client
    client = WebClient(token=token)


def find_channel_id(channel_name):
    conversation_id = None
    try:
        for result in client.conversations_list():
            if conversation_id is not None:
                break
            for channel in result["channels"]:
                if channel["name"] == channel_name:
                    conversation_id = channel["id"]
                    break
        return conversation_id

    except SlackApiError as e:
        print(f"Error: {e}")


def send_message(text, channel_id):
    try:
        client.chat_postMessage(
            channel=channel_id,
            text=text
        )

    except SlackApiError as e:
        print(f"Error: {e}")


if __name__ == '__main__':

    # Get token
    with open('config.json') as fi:
        config = json.load(fi)
        slack_token = config['slack_notification'].get('token')

    connect_client(slack_token)
    channel_id = find_channel_id('général')
    send_message("Test", channel_id)
