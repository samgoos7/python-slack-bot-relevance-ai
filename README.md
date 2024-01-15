# Slack to Relevance AI Integration

This repository contains the code to run a Flask app that connects Slack with an AI agent from Relevance AI. Follow the instructions below to set up and configure the integration.

## Requirements

Before you begin, make sure you have the following:

- A Slack workspace and a channel where you want to integrate the AI agent.
- A Relevance AI account.
- An existing agent created in Relevance AI.

## Slack Setup

1. Go to [Slack API](https://api.slack.com/) and log in or create an account if you haven't already. Once logged in, navigate to "Your apps."
2. Click on "Create New App" and start from scratch. Give your app a name and choose the workspace where you want your app to reside.
3. In the left panel, navigate to "OAuth & Permissions."
4. Under "Bot Token Scopes," add the following permissions:
   - chat:write
   - app_mentions:read
   - chat:write
   - files:read
5. Click "Install to Workspace." After your app is installed, a Bot User OAuth Token will be generated. Save this token securely.
6. Navigate to "Basic Information" and copy the signing secret. Store this signing secret safely.

## App Setup in Replit

1. Go to [Replit](https://replit.com/) and fork the [Python-Whatsapp-Bot-x-Relevance-AI](https://replit.com/@SamGoos/Python-Slack-Bot-x-Relevance-AI) project.
2. In your project's secrets, add your Bot Token from Slack as `SLACK_TOKEN` and the Signing Secret as `SIGNING_SECRET`.
3. Run the app. In the web view tab, click "New Tab," and copy the URL of that new tab.

## Webhook Connection

1. Return to the Slack API and navigate to "Event Subscriptions." Click "Enable Events."
2. Paste the Replit URL into the "Request URL" field, and add `/slack/events` to the URL.
3. Wait until it's verified.
4. Reinstall the app into your Slack workspace.

## Relevance Agent Setup

1. Go to [Relevance AI](https://relevance.ai/) and log in to your account.
2. Navigate to the "API Keys" tab on the left side of the screen.
3. Scroll down and click on "+ Create New Secret Key."
4. Copy the region ID, the project ID, and the authentication token. Store them securely.
5. Go to your Relevance AI agent and open the conversation panel. In the URL, the second-to-last string is your agent ID. For example: `app.relevanceai.com/agents/xxxx/agent_id/xxxx`.
6. Return to Replit and paste these four keys into the corresponding fields in the secrets tab.

## Testing the Application

1. Go to your Slack app, and you should see it listed under the "Apps" section on the left side of the screen.
2. Integrate your app into your preferred channel.
3. When mentioning the app in the channel, it should respond in that thread. Subsequent messages in that thread will continue the conversation with the agent.
4. Threads and messages should also be visible in your Relevance AI agent interface.

Enjoy using the Slack to Relevance AI integration!