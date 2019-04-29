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
# ratings_{groupid}
# ratings_{userid}

ENTRY_GROUP = 'group'
# chinfo_{groupid}


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


def extract_entry(event):
    if event.source.type == 'group':
        return ENTRY_RATINGS + '_' + event.source.group_id
    return ENTRY_RATINGS + '_' + event.source.user_id


def delete_entry(event):
    r_entry = extract_entry(event)
    ratings = load_ordered_dict(r_entry)

    splitted = event.message.text.split()
    if len(splitted) < 2:
        app.logger.warn('too short message to demote')
        return

    to_delete = splitted[1]
    if to_delete in ratings:
        del ratings[to_delete]
        message = '삭제되었습니다'

        ratings_entry = json.dumps(ratings)
        r.set(r_entry, ratings_entry)
    else:
        message = '삭제할 수 없습니다'

    message = ratings_to_message(ratings) + '\n\n' + message
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def load_ordered_dict(key):
    try:
        value_txt = r.get(key)
        ordered_dict = json.loads(value_txt, object_pairs_hook=OrderedDict)
    except Exception as e:
        app.logger.exception(e)
        ordered_dict = OrderedDict()

    return ordered_dict


def adjust_ranking(action, event):
    '''
    ** event example **
    {"message": {"id": "9760259091048", "text": "\ubaa8\ubc14\uc77c \ub77c\uc778\uc5d0\uc120 \ubcfc\ub4dc\uac00 \uc5c6\ub098\ubd04", "type": "text"},
     "replyToken": "4b35e226593e42a7ba0f53fd34b4a71b",
     "source": {"groupId": "C96673d1530d37de2b0a8ffc2e5df5f1f", "type": "group", "userId": "U13990d12ea3aa82eef9e01fcea9a963f"},
     "timestamp": 1556272465993, "type": "message"}
     '''

    r_entry = extract_entry(event)
    ratings = load_ordered_dict(r_entry)

    splitted = event.message.text.split()

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
    r.set(r_entry, ratings_entry)

    message = ratings_to_message(ratings)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def show_ranking(event):
    r_entry = extract_entry(event)
    ratings = load_ordered_dict(r_entry)
    message = ratings_to_message(ratings)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def update_message_frequency(event):
    group_key = '{}_{}'.format(ENTRY_GROUP, event.source.group_id)
    member_info = load_ordered_dict(group_key)
    user_id = event.source.user_id
    if user_id in member_info:
        member_info[user_id]['n_message'] += 1
    else:
        member_info[user_id] = {'n_message': 1}

    member_info_bytes = json.dumps(member_info)
    r.set(group_key, member_info_bytes)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if len(event.message.text) == 0:
        app.logger.warn('too short message to split: ' + event.message.text)
        return

    if event.source.type == 'group':
        update_message_frequency(event)

    if '!' in event.message.text:
        app.logger.info(event)

    splitted = event.message.text.split()
    if '!도움' in event.message.text:
        message = '*demoter_bot*\n\n' + \
            '*!도움* 도움말 보기\n' + \
            '*!등급* 당원 등급을 조회합니다\n' + \
            '*!강등 @아이디 등급* 당원을 강등합니다\n' + \
            '*!승급 @아이디 등급* 당원을 승급합니다\n' + \
            '*!삭제 @아이디* 당원을 삭제합니다'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))

    if splitted[0] == '!reset':
        r_entry = extract_entry(event)
        r.delete(r_entry)
        message = '리셋되었습니다'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))

    if splitted[0] == '!삭제':
        delete_entry(event)

    if splitted[0] == '!강등':
        adjust_ranking('demote', event)

    if splitted[0] == '!승급':
        adjust_ranking('promote', event)

    if splitted[0] == '!등급':
        show_ranking(event)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
