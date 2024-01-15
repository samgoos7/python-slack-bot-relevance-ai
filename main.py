import os
import slack
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests
from slackeventsapi import SlackEventAdapter
import time
import logging

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(os.environ['SIGNING_SECRET'], '/slack/events', app)

client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']

# Relevance AI environment variables
authorization_token = os.environ['RELEVANCE_AI_AUTH_TOKEN']
agent_id = os.environ['RELEVANCE_AI_AGENT_ID']
region = os.environ['RELEVANCE_AI_REGION']
project_id = os.environ['RELEVANCE_AI_PROJECT_ID']

thread_conversation_data = {}
processed_events = set()

# Function to trigger Relevance AI agent with first message
def trigger_agent(content):
    headers = {
        "Authorization": authorization_token,
        "Content-Type": "application/json"
    }
  
    trigger_payload = {
        "message": {
            "role": "user",
            "content": content
        },
        "agent_id": agent_id
    }
  
    trigger_url = f"https://api-{region}.stack.tryrelevance.com/latest/agents/trigger"
    trigger_response = requests.post(trigger_url, headers=headers, json=trigger_payload)
  
    if trigger_response.status_code == 200:
        return trigger_response.json()  # Return the whole JSON response
    else:
        return None

# Function to poll response from Relevance AI agent      
def poll_response(studio_id, job_id):
    headers = {
        "Authorization": authorization_token,
        "Content-Type": "application/json"
    }
    
    poll_url = f"https://api-{region}.stack.tryrelevance.com/latest/studios/{studio_id}/async_poll/{job_id}"
    
    max_retries = 30  # Adjust as needed
    attempt = 0
    poll_interval = 2  # Adjust as needed
    
    while attempt < max_retries:
        poll_response = requests.get(poll_url, headers=headers)
        if poll_response.status_code == 200:
            poll_response_data = poll_response.json()
            updates = poll_response_data.get('updates')
            if updates and any(update.get('type') == "chain-success" for update in updates):
                for update in updates:
                    if update.get('type') == 'chain-success':
                        answer = update.get('output', {}).get('output', {}).get('answer', '')
                        if answer:
                            return answer, 200
        attempt += 1
        time.sleep(poll_interval)

    return "No valid response received after polling attempts.", 500

# Function to send a message to thread of Relevance AI agent conversation
def add_message_to_conversation(content, conversation_id, channel_id, thread_ts):
    headers = {
        "Authorization": authorization_token,
        "Content-Type": "application/json"
    }
  
    trigger_payload = {
        "message": {
            "role": "user",
            "content": content
        },
        "agent_id": agent_id,
        "conversation_id": conversation_id
    }
  
    trigger_url = f"https://api-{region}.stack.tryrelevance.com/latest/agents/trigger"
    trigger_response = requests.post(trigger_url, headers=headers, json=trigger_payload)
  
    if trigger_response.status_code == 200:
        trigger_data = trigger_response.json()
        if 'job_info' in trigger_data:
            studio_id = trigger_data['job_info'].get('studio_id')
            job_id = trigger_data['job_info'].get('job_id')
            poll_result = poll_response(studio_id, job_id)
            if poll_result[1] == 200:
                response_message = poll_result[0]
                send_response_message(channel_id, thread_ts, response_message)
            else:
                send_response_message(channel_id, thread_ts, "Failed to get a response from the agent.")
    else:
        send_response_message(channel_id, thread_ts, "Failed to add message to the conversation.")

# Function to send a message to the channel
def send_response_message(channel_id, thread_ts, response_message):
    conversation_details = thread_conversation_data.get(thread_ts, {})
    user_id = conversation_details.get('user_id')
    mention = f"<@{user_id}> " if user_id else ""
    client.chat_postMessage(channel=channel_id, text=mention + response_message, thread_ts=thread_ts)

# Handle messages in Slack  
@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    event_id = payload.get('event_id')
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')
    ts = event.get('ts')
    thread_ts = event.get('thread_ts', ts)

    if user_id == BOT_ID:
        logging.debug("Ignoring bot's own message")
        return

    if event_id in processed_events:
        logging.debug("Ignoring duplicate event: %s", event_id)
        return

    processed_events.add(event_id)

    if thread_ts not in thread_conversation_data:
        if f"<@{BOT_ID}>" in text:
            trigger_data = trigger_agent(text)
            if trigger_data and 'job_info' in trigger_data:
                studio_id = trigger_data['job_info'].get('studio_id')
                job_id = trigger_data['job_info'].get('job_id')
                conversation_id = trigger_data.get('conversation_id')
                thread_conversation_data[thread_ts] = {
                    'studio_id': studio_id, 
                    'job_id': job_id, 
                    'conversation_id': conversation_id,
                    'user_id': user_id,  # Storing user ID
                    'processed_messages': set([ts])
                }

                poll_result = poll_response(studio_id, job_id)
                if poll_result[1] == 200:
                    response_message = poll_result[0]
                    send_response_message(channel_id, thread_ts, response_message)
                else:
                    send_response_message(channel_id, thread_ts, "Failed to get a response from the agent.")
    else:
        conversation_details = thread_conversation_data[thread_ts]
        processed_messages = conversation_details.get('processed_messages', set())

        if ts not in processed_messages:
            conversation_details['user_id'] = user_id  # Update user ID
            processed_messages.add(ts)
            conversation_details['processed_messages'] = processed_messages

            add_message_to_conversation(text, conversation_details['conversation_id'], channel_id, thread_ts)

    logging.debug("Processed the message with timestamp: %s", ts)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)



