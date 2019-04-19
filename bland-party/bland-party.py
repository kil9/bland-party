import json
from collections import OrderedDict

from flask import request, abort

from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

from config import app, r, line_bot_api, handler

ENTRY_RATINGS = 'ratings'


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if len(event.message.text) == 0:
        app.logger.warn('too short message to split: ' + event.message.text)
        return

    splitted = event.message.text.split()
    if splitted[0] == '!리셋':
        r.delete(ENTRY_RATINGS)

    if splitted[0] == '!강등':
        demote(event)


def ratings_to_message(ratings):
    str = ''
    for person, rating in ratings.items():
        str += '{} {}\n'.format(rating, person)
    return str


def demote(event):

    splitted = event.message.text.split()
    try:
        ratings_txt = r.get(ENTRY_RATINGS)
        ratings = json.loads(ratings_txt, object_pairs_hook=OrderedDict)
    except Exception as e:
        app.logger.exception(e)
        ratings = OrderedDict()

    if len(splitted) < 3:
        app.logger.warn('too short message to demote')
        return

    if len(splitted) >= 3:
        to_demote = splitted[1]
        demote_rating = splitted[2]

    if to_demote in ratings:
        del ratings[to_demote]

    ratings[to_demote] = demote_rating

    message = ratings_to_message(ratings)

    ratings_entry = json.dumps(ratings)
    r.set(ENTRY_RATINGS, ratings_entry)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message))


if __name__ == "__main__":
    app.run(host='0.0.0.0')
