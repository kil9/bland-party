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


def ratings_to_message(ratings):
    str = ''
    for person, rating in ratings.items():
        str += '{} {}\n'.format(rating, person)
    return str


def delete_entry(event):
    splitted = event.message.text.split()
    try:
        ratings_txt = r.get(ENTRY_RATINGS)
        ratings = json.loads(ratings_txt, object_pairs_hook=OrderedDict)
    except Exception as e:
        app.logger.exception(e)
        ratings = OrderedDict()

    if len(splitted) < 2:
        app.logger.warn('too short message to demote')
        return

    to_delete = splitted[1]
    if to_delete in ratings:
        del ratings[to_delete]
        message = '삭제되었습니다'

        ratings_entry = json.dumps(ratings)
        r.set(ENTRY_RATINGS, ratings_entry)
    else:
        message = '삭제할 수 없습니다'

    message += '\n\n' + ratings_to_message(ratings)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


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
        to_demote = splitted[1:-1]
        to_demote = ' '.join(to_demote)
        demote_rating = splitted[-1]

    if to_demote in ratings:
        del ratings[to_demote]

    ratings[to_demote] = demote_rating

    ratings_entry = json.dumps(ratings)
    r.set(ENTRY_RATINGS, ratings_entry)

    message = ratings_to_message(ratings)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if len(event.message.text) == 0:
        app.logger.warn('too short message to split: ' + event.message.text)
        return

    splitted = event.message.text.split()
    if splitted[0] == '!리셋':
        r.delete(ENTRY_RATINGS)
        message = '리셋되었습니다'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))

    if splitted[0] == '!삭제':
        delete_entry(event)

    if splitted[0] == '!강등':
        demote(event)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
