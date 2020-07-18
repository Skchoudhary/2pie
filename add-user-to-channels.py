import os
import hmac
import hashlib
import configparser
import datetime

from flask import abort, Flask, jsonify, request

app = Flask(__name__)
configParser = configparser.ConfigParser()
configParser.read('./bot.config')

def is_request_valid(request):
    """
    check to see requesting comming from the valid slack bot.
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


@app.route('/add-user', methods=['Post'])
def add_users_to_channels():
    """
    add the given user to the common channels in the workspace
    """
    if not is_request_valid(request):
       abort(400)

    return jsonify(
        response_type='in_channel',
        text='Hello bro!',
    )

