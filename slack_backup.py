#!/usr/bin/python3
# Code initially based on
# https://gist.github.com/benoit-cty/a5855dea9a4b7af03f1f53c07ee48d3c

import urllib.request, urllib.parse
from urllib.error import HTTPError
import http.client
from random import randint
from time import sleep
import requests
import json
import os
import re
TOKEN = os.environ['TOKEN']  # provide bot or user token (preferably user)
FILE_TOKEN = os.environ.get('FILE_TOKEN')  # file access token via public dump
DOWNLOAD = os.environ.get('DOWNLOAD')
os.makedirs('backup', mode=0o700, exist_ok=True)

users = type('test', (), {})()

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

def format_name(x):
  name = x.lower()
  name = re.sub(r'[^a-z0-9_-]+', '_', name)
  name = re.sub(r'_+', '_', name)
  return name

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
      try:
        result = client.conversations_history(channel=channel_id, cursor=result['response_metadata']['next_cursor'])
        all_messages += result["messages"]

        # take a nap
        sleep(1)
      except http.client.IncompleteRead as e:
        print(f'IncompleteRead {channel_name}')
      except Exception as result:
        print("Unknown error" + str(result))
    print(f'  Downloaded {len(all_messages)} messages from {channel_name}.')

    # Rewrite private URLs to have token, like Slack's public dump
    filenames = {'all.json'}  # avoid overwriting json
    count = 0
    for message in all_messages:

      # define a message by its client_msg_id, or default to the ts (Slack's weird timestamp)
      msg_id = message.get('client_msg_id', message.get('ts'))

      # if there is no msg_id for whatever reason
      if msg_id == 'none':
          print(f' {message} ')

      if 'files' in message:

        # create the backup/<channel>/<msg_id> directory, so we can put files in there
        # and persist the file names that were originally set, they display inline!
        os.makedirs(f'backup/{channel_name}/{msg_id}', mode=0o700, exist_ok=True)

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
                try:
                  # https://api.slack.com/types/file#authentication
                  with urllib.request.urlopen(urllib.request.Request(value,
                        headers={'Authorization': 'Bearer ' + TOKEN})) as infile:
                    with open(f'backup/{channel_name}/{msg_id}/{filename}', 'wb') as outfile:
                      outfile.write(infile.read())
            # if (key.startswith('url_private') and isinstance(value, str)) and value.startswith('https://'):
            #   if DOWNLOAD and not key.endswith('_download'):
            #     filename = os.path.basename(urllib.parse.urlparse(value).path)
            #     filenames.add(filename)
            #     # https://api.slack.com/types/file#authentication
            #     try:
            #       r = requests.get(file[key], headers={'Authorization': 'Bearer %s' % TOKEN})
            #       r.raise_for_status
            #       file_data = r.content   # get binary content

            #       # save file to disk
            #       with open(f'backup/{channel_name}/{msg_id}/{filename}' , 'w+b') as outfile:
            #         outfile.write(bytearray(file_data))
                except http.client.IncompleteRead as e:
                  print(f' incomplete read {file[key]}')
                  outfile.write(e.partial)
                except FileNotFoundError as e:
                  print(f' FileNotFoundError: {e} ')
                  print(f' Error getting file: {filename}, from url {file[key]} ')
                except HTTPError as e:
                  print(f' HTTPError: {e} ')
                except Exception as e:
                  print(f' Unknown: {e} ')

                # file[key + '_file'] = f'{channel_name}/{filename}'
                file[key + '_file'] = f'{channel_name}/{msg_id}/{filename}'
                

          # avoid slacks rate limit and/or timeouts, take a quick nap
          sleep(randint(1,3))

    verbs = []
    if DOWNLOAD: verbs.append('Downloaded')
    if FILE_TOKEN: verbs.append('Linked')
    if verbs: print(f'  {" & ".join(verbs)} {count} files from messages in {channel_name}.')

    # if count:
    save_json(all_messages, f'backup/{channel_name}/all.json')

  except SlackApiError as e:
      print("Error using conversation: {}".format(e))

def backup_all_channels():
  try:
    print('Listing channels')
    result = client.conversations_list(
        types="public_channel, private_channel, mpim, im",
        # types="mpim, im",
        limit=1000,
    )
    channels = result['channels']
    print(f'  Got {len(channels)} channels')
    for channel in channels:
      result = client.conversations_members(
        channel=channel['id'],
      )
      channel['members'] = result['members']

      if "name" in channel:
        channel["name"] = format_name(channel["name"])
      else:
        member_name_list = []
        for user_id in channel["members"]:
          el = [x for x in users if x["id"] == user_id][0]
          member_name_list.append(el["name"])

        members_list = '-'.join(member_name_list)
        if channel["user"] not in channel["members"]:
          members_list += "-" + channel["user"]
        members_list += "-" + channel["id"]

        channel["name"] = format_name(members_list)

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
    global users
    users = result['members']
    print(f'  Got {len(users)} users')
  except SlackApiError as e:
    print("Error using conversation: {}".format(e))
    return
  save_json(users, 'backup/users.json')

if __name__ == "__main__":
  backup_all_users()
  backup_all_channels()