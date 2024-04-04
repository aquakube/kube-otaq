import json
import logging
import os
import datetime

import yaml
import requests

logger = logging.getLogger(__name__)

def send_google_message(google_webhook: str, resource: dict, state: dict, workflow_success: bool):
    message = {
        "cardsV2": [
            {
                "cardId": "card_one",
                "card": {
                    "header": {
                        "title": f"Provisioning OTAQ '{resource['metadata']['name']}' {workflow_success}!",
                        "subtitle": f"{datetime.datetime.utcnow().isoformat()} UTC"
                    },
                    "sections": [
                        {
                            "widgets": [
                                {
                                    "textParagraph": {
                                        "text": f"{yaml.safe_dump(resource)}"
                                    }
                                },
                            ]
                        }
                    ]
                }
            }
        ]
    }

    if state.get('error') is not None:
        message['cardsV2'][0]['card']['sections'].append({
            "widgets": [
                {
                    "textParagraph": {
                        "text": state["error"]
                    }
                },
            ]
        })

    requests.post(
        google_webhook,
        data=json.dumps(message),
        headers={"Content-Type": "application/json; charset=UTF-8"}
    )


def send_slack_message(slack_webhook: str, resource: dict, state: dict, workflow_success: bool):
    message = {
        "icon_emoji": ":robot_face:",
        "username": "Provisioning Bot",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"""
Provisioning OTAQ '{resource['metadata']['name']}' {workflow_success}!
{datetime.datetime.utcnow().isoformat()} UTC
                    """
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"""
                        ```
{yaml.safe_dump(resource)}
                        ```
                    """
                }
            }
        ]
    }

    if state.get('error') is not None:
        message['blocks'].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": state["error"]
            }
        }) 
    
    requests.post(
        slack_webhook,
        data=json.dumps(message),
        headers={"Content-Type": "application/json; charset=UTF-8"}
    )


def run(resource: dict):
    
    state = {}
    with open('/tmp/state.json', 'r') as f:
        state = json.load(f)

    workflow_success = os.getenv("WORKFLOW_STATUS")

    # send slack message
    slack_webhook = os.getenv("SLACK_WEBHOOK")
    send_slack_message(slack_webhook, resource, state, workflow_success)

    # send google chat message
    google_webhook = os.getenv("GOOGLE_WEBHOOK")
    send_google_message(google_webhook, resource, state, workflow_success)
