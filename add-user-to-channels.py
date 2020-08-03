import os
import hmac
import hashlib
import configparser
import datetime
import json
import requests

from flask import abort, Flask, jsonify, request
from slack import WebClient
from slack.errors import SlackApiError

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['TESTING'] = True
configParser = configparser.ConfigParser()
configParser.read('./bot.config')

client = WebClient(token=configParser.get('bot', 'SLACK_ACCESS_TOKEN'))

def is_request_valid(request):
    """
    check to see requesting comming from the slack.
    """
    request_body = request.get_data().decode('utf-8')
    timestamp = request.headers['X-Slack-Request-Timestamp']
    if abs(int(datetime.datetime.now().timestamp()) - int(timestamp)) > 60 * 5:
    # The request timestamp is more than five minutes from local time.   
    # It could be a replay attack, so let's ignore it.                   
        return

    slack_signature = request.headers['X-Slack-Signature']
    slack_signing_secret = bytes(configParser.get('bot', 'SLACK_SIGNING_SECRET'), 'latin-1')
    sig_basestring = f'v0:{timestamp}:{str(request_body)}'
    my_signature = 'v0=' + hmac.new(
        slack_signing_secret,
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(my_signature, slack_signature)


def conversation_list():
    """
    fetch the list of the public conversation from workspace.
    """
    converstaions = []
    try:
        response = client.conversations_list()
        conversations = response['channels']
    except SlackApiError as e:
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")

    return conversations
    

def add_users_to_channels(sub_command, response_url):
    """
    add the given user to the common channels in the workspace
    """
    users = sub_command.split(',')
    channels = conversation_list()
    print(users)
    users_id = [str(user.split('|')[0]).replace('<@', '') for user in users if '|' in user]
    users_id_str = ','.join(users_id)
    print(users_id_str)
    channels_name = []
    for channel in channels:
        if channel['is_channel']:
            print(f'channel name: {channel["name"]}')
            try:
                response = client.conversations_invite(channel=channel['id'], users=users_id_str)
                if response['ok']:
                    channels_name.append(channel['name'])
            except SlackApiError as e:
                print(e)
                    
    data = {
        'response_type': 'in_channel',
        'text': f'User(s) added to the channels({",".join(channels_name)})'
    }
    requests.post(response_url, json=data)
    return True
        
@app.route('/add-user', methods=['Post'])
def slack_slash_commands():
    """

    """
    if not is_request_valid(request):
       abort(400)

    print(request.form)
    command = request.form['command']
    sub_command = request.form['text']
    response_url = request.form['response_url']
    
    if command == '/add-user':
        
        if not sub_command:
            return jsonify(
                response_type='in_channel',
                text='no user(s) passed to add in channels.'
            )

        if sub_command == 'help':
            return jsonify(
                response_type='in_channle',
                text="Add passed user to the list of public channels"
            )

        add_users_to_channels(sub_command, response_url)
    return jsonify(
            response_type='in_channel',
            text='adding user to the public channel...'
        )

        
