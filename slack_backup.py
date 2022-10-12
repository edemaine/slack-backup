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
indent = 0

def slack_list(field, info, operation, **dargs):
  # Most WebClient methods are paginated, returning the first n results
  # along with a "next_cursor" pointer to fetch the rest.
  print(f'{" " * indent}Fetching {info or field}...')
  try:
    items = []
    cursor = None
    while True:
      result = operation(cursor=cursor, **dargs)
      items += result[field]
      if 'response_metadata' not in result: break
      cursor = result['response_metadata']['next_cursor']
      if not cursor: break
      print(f'{" " * indent}  Fetching more...')
    print(f'{" " * indent}  Fetched {len(items)} {field}')
  except SlackApiError as e:
    print("ERROR USING CONVERSATION: {}".format(e))
  return items

def all_channels():
  return slack_list('channels', 'all channels',
    client.conversations_list, types='public_channel, private_channel')

def all_channel_members(channel):
  return slack_list('members', f'all members in channel {channel["name"]}',
    client.conversations_members, channel=channel['id'])

def all_channel_messages(channel):
  return slack_list('messages', f'all messages from channel {channel["name"]}',
    client.conversations_history, channel=channel['id'])

def all_users():
  return slack_list('members', 'all users', client.users_list)

import json
def save_json(data, filename):
  print('  Saving to', filename)
  os.makedirs(os.path.dirname(filename), mode=0o700, exist_ok=True)
  with open(filename, 'w') as outfile:
    json.dump(data, outfile, indent=2)

def backup_channel(channel):
  try:
    all_messages = all_channel_messages(channel)
    save_json(all_messages, f'backup/{channel["name"]}/all.json')

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
                  with open(f'backup/{channel["name"]}/{filename}', 'wb') as outfile:
                    outfile.write(infile.read())
                file[key + '_file'] = f'{channel["name"]}/{filename}'
    verbs = []
    if DOWNLOAD: verbs.append('Downloaded')
    if FILE_TOKEN: verbs.append('Linked')
    if verbs: print(f'  {" & ".join(verbs)} {count} files from messages in {channel["name"]}.')

  except SlackApiError as e:
      print("Error using conversation: {}".format(e))

def backup_all_channels():
  global indent
  channels = all_channels()
  indent += 2
  for channel in channels:
    channel['members'] = all_channel_members(channel)
  indent -= 2
  save_json(channels, 'backup/channels.json')
  for channel in channels:
    backup_channel(channel)

def backup_all_users():
  users = all_users()
  save_json(users, 'backup/users.json')

if __name__ == "__main__":
  backup_all_users()
  backup_all_channels()
