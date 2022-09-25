#!/usr/bin/python3
# Code initially based on
# https://gist.github.com/benoit-cty/a5855dea9a4b7af03f1f53c07ee48d3c

import urllib.request, urllib.parse

import os
TOKEN = os.environ['TOKEN']  # provide bot or user token (preferably user)
FILE_TOKEN = os.environ.get('FILE_TOKEN')  # file access token via public dump
DOWNLOAD = os.environ.get('DOWNLOAD')
os.makedirs('backup', mode=0o700, exist_ok=True)

# Import Slack Python SDK (https://github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

client = WebClient(token=TOKEN)

import json
def save_json(data, filename):
  print('  Saving to', filename)
  os.makedirs(os.path.dirname(filename), mode=0o700, exist_ok=True)
  with open(filename, 'w') as outfile:
    json.dump(data, outfile, indent=2)

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
    print(f'  Downloaded {len(all_messages)} messages from {channel_name}.')

    save_json(all_messages, f'backup/{channel_name}/all.json')

    # Rewrite private URLs to have token, like Slack's public dump
    filenames = {'all.json'}  # avoid overwriting json
    count = 0
    for message in all_messages:
      if 'files' in message:
        for file in message['files']:
          count += 1
          for key, value in list(file.items()):
            if (key.startswith('url_private') or key.startswith('thumb')) \
               and isinstance(value, str) and value.startswith('https://'):
              if FILE_TOKEN:
                file[key] = value + '?t=' + FILE_TOKEN
              if DOWNLOAD and not key.endswith('_download'):
                filename = os.path.basename(urllib.parse.urlparse(value).path)
                if filename in filenames:
                  i = 0
                  base, ext = os.path.splitext(filename)
                  def rewrite():
                    return base + '_' + str(i) + ext
                  while rewrite() in filenames:
                    i += 1
                  filename = rewrite()
                filenames.add(filename)
                # https://api.slack.com/types/file#authentication
                with urllib.request.urlopen(urllib.request.Request(value,
                       headers={'Authorization': 'Bearer ' + TOKEN})) as infile:
                  with open(f'backup/{channel_name}/{filename}', 'wb') as outfile:
                    outfile.write(infile.read())
                file[key + '_file'] = f'{channel_name}/{filename}'
    verbs = []
    if DOWNLOAD: verbs.append('Downloaded')
    if FILE_TOKEN: verbs.append('Linked')
    if verbs: print(f'  {" & ".join(verbs)} {count} files from messages in {channel_name}.')

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
  save_json(channels, 'backup/channels.json')
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
  save_json(users, 'backup/users.json')

if __name__ == "__main__":
  backup_all_users()
  backup_all_channels()
