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

from utils import rreplace


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
        str += '{} {}\n'.format(person, rating)
    rreplace(str, '\n', '', 1)
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

    message = ratings_to_message(ratings) + '\n\n' + message
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def adjust_ranking(action, event):
    splitted = event.message.text.split()
    try:
        ratings_txt = r.get(ENTRY_RATINGS)
        ratings = json.loads(ratings_txt, object_pairs_hook=OrderedDict)
    except Exception as e:
        app.logger.exception(e)
        ratings = OrderedDict()

    if len(splitted) < 3:
        app.logger.warn('too short message to promote/demote')
        return

    if len(splitted) >= 3:
        to_adjust = splitted[1:-1]
        to_adjust = ' '.join(to_adjust)
        ranking_title = splitted[-1]

    if to_adjust in ratings:
        del ratings[to_adjust]

    ratings[to_adjust] = ranking_title
    if action == 'promote':
        ratings.move_to_end(to_adjust, last=False)

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
    if '!도움' in event.message.text:
        message = '*demoter_bot*\n\n' + \
            '*!도움* 도움말 보기\n' + \
            '*!강등 @아이디 등급* 당원을 강등합니다\n' + \
            '*!승급 @아이디 등급* 당원을 승급합니다\n' + \
            '*!삭제 @아이디* 당원을 삭제합니다\n'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))

    if splitted[0] == '!reset':
        r.delete(ENTRY_RATINGS)
        message = '리셋되었습니다'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))

    if splitted[0] == '!삭제':
        delete_entry(event)

    if splitted[0] == '!강등':
        adjust_ranking('demote', event)

    if splitted[0] == '!승급':
        adjust_ranking('promote', event)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
