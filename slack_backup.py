# Initially based on
# https://gist.github.com/benoit-cty/a5855dea9a4b7af03f1f53c07ee48d3c

'''
Script to archive Slack messages from a channel list.
You have to create a Slack Bot and invite him to private channels.
View https://github.com/docmarionum1/slack-archive-bot for how to configure your account.
Then provide the bot token to this script with the list of channels.
'''

import os
TOKEN = os.environ['TOKEN']  # provide bot or user token (preferably user)
os.makedirs('backup', mode=0o700, exist_ok=True)

# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import json

# WebClient insantiates a client that can call API methods
# When using Bolt, you can use either `app.client` or the `client` passed to listeners.
client = WebClient(token=TOKEN)

def backup_channel(channel_name, channel_id):
  try:
    print('Getting messages from', channel_name)
    # Call the conversations.history method using the WebClient
    # conversations.history returns the first 100 messages by default
    # These results are paginated
    result = client.conversations_history(channel=channel_id)
    all_messages = []
    all_messages += result["messages"]
    while result['has_more']:
      print("\tGetting more...")
      result = client.conversations_history(channel=channel_id, cursor=result['response_metadata']['next_cursor'])
      all_messages += result["messages"]
    # Save to disk
    os.makedirs(f'backup/{channel_name}', mode=0o700, exist_ok=True)
    filename = f'backup/{channel_name}/all.json'
    print(f'  We have downloaded {len(all_messages)} messages from {channel_name}.')
    print('  Saving to', filename)
    with open(filename, 'w') as outfile:
      json.dump(all_messages, outfile, indent=2)
  except SlackApiError as e:
      print("Error using conversation: {}".format(e))

def backup_all_channels():
  try:
    print('Listing channels')
    result = client.conversations_list(
        types="public_channel, private_channel",
        limit=1000,
    )
    channels = result['channels']
    print(f'  Got {len(channels)} channels')
    for channel in channels:
      result = client.conversations_members(
        channel=channel['id'],
      )
      channel['members'] = result['members']
      print(f'  Got {len(result["members"])} members for channel {channel["name"]}')
  except SlackApiError as e:
    print("Error using conversation: {}".format(e))
    return
  filename = 'backup/channels.json'
  print('  Saving to', filename)
  with open(filename, 'w') as outfile:
    json.dump(channels, outfile, indent=2)
  for channel in channels:
    backup_channel(channel['name'], channel['id'])

def backup_all_users():
  try:
    print('Listing users')
    result = client.users_list()
    users = result['members']
    print(f'  Got {len(users)} users')
  except SlackApiError as e:
    print("Error using conversation: {}".format(e))
    return
  filename = 'backup/users.json'
  print('  Saving to', filename)
  with open(filename, 'w') as outfile:
    json.dump(users, outfile, indent=2)

if __name__ == "__main__":
  backup_all_users()
  backup_all_channels()
