import json
import random
from collections import OrderedDict

from flask import request, abort

from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

from config import app, r, line_bot_api, handler

from utils import rreplace, load_ordered_dict


ENTRY_RATINGS = 'ratings'
# ratings_{group_id}
# ratings_{user_id}

ENTRY_GROUP = 'group'
# group_{group_id}


@app.route("/groups/<group_id>", methods=['DELETE'])
def reset_group(group_id, is_key=False):
    if is_key:
        group_key = group_id
    else:
        group_key = '{}_{}'.format(ENTRY_GROUP, group_id)
    app.logger.info('delete key: {}'.format(group_key))
    r.delete(group_key)

    return 'ok'


@app.route("/groups", methods=['DELETE'])
def reset_all_groups():
    s, scanned = r.scan(0, ENTRY_GROUP + '*')
    group_ids = (b.decode('utf-8') for b in scanned)
    for group_id in group_ids:
        reset_group(group_id, is_key=True)

    return 'ok'


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
        message = '삭제되었습니다 😌'

        ratings_entry = json.dumps(ratings)
        r.set(r_entry, ratings_entry)
    else:
        message = '삭제할 수 없습니다 😵'

    message = ratings_to_message(ratings) + '\n\n' + message
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def adjust_ranking(action, event):
    '''
    ** event example **
    {"message": {"id": "9760259091048", "text": "text text", "type": "text"},
     "replyToken": "4b35e226593e42a7ba0f53fd34b4a71b",
     "source": {"groupId": "C96673d1530d37de2b0a8ffc2e5df5f1f",
                "type": "group",
                "userId": "U13990d12ea3aa82eef9e01fcea9a963f"},
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
    rating_key = extract_entry(event)
    ratings = load_ordered_dict(rating_key)
    message = ratings_to_message(ratings)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def show_today_message(event):
    group_id = event.source.group_id
    group_key = '{}_{}'.format(ENTRY_GROUP, event.source.group_id)
    member_info = load_ordered_dict(group_key)

    filtered = filter(lambda x: 'message_today' in x[1], list(member_info.items()))

    user_id, user_info = random.choice(list(filtered))
    profile = line_bot_api.get_group_member_profile(group_id, user_id)
    message = '*오늘의 명언*\n\n'
    message += '{}: {}'.format(profile.display_name, user_info['message_today'])
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def show_frequency(event):
    group_id = event.source.group_id
    group_key = '{}_{}'.format(ENTRY_GROUP, event.source.group_id)
    member_info = load_ordered_dict(group_key)

    message_frequency = OrderedDict()
    for user_id, user_info in member_info.items():
        profile = line_bot_api.get_group_member_profile(group_id, user_id)
        message_frequency[profile.display_name] = user_info['n_message']

    sorted_users = sorted(message_frequency.items(), key=lambda m: m[1], reverse=True)

    sum_messages = sum((m[1] for m in sorted_users))

    message = '*오늘의 메시지 수 🎤*\n\n'
    for i, (user_name, frequency) in enumerate(sorted_users):
        medals = {0: '🥇', 1: '🥈', 2: '🥉'}
        if i in medals:
            message += '{} '.format(medals[i])
        message += '{0}: {1}회 ({2:.1f}%)\n'.format(
                user_name, frequency, frequency/sum_messages*100.0)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def has_to_change_message(entry, message):
    if message.startswith('!'):
        return False

    if 'message_today' not in entry:
        return True

    if random.randint(0, entry['n_message']) == 0:
        return True
    elif len(message) > len(entry['message_today']) and random.randint(0, entry['n_message']) == 0:
        return True

    return False


def message_preprocess(event):
    group_key = '{}_{}'.format(ENTRY_GROUP, event.source.group_id)
    member_info = load_ordered_dict(group_key)
    user_id = event.source.user_id

    message = event.message.text
    if user_id not in member_info:
        member_info[user_id] = {'n_message': 0, 'message_today': message}
    else:
        if has_to_change_message(member_info[user_id], message):
            member_info[user_id]['message_today'] = message

    member_info[user_id]['n_message'] += 1
    member_info_serialized = json.dumps(member_info)

    r.setex(group_key, 86400, member_info_serialized)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    app.logger.info(event)
    __import__('pprint').pprint(event)

    if len(event.message.text) == 0:
        app.logger.warn('too short message to split: ' + event.message.text)
        return

    if event.source.type == 'group':
        message_preprocess(event)

    if '!' in event.message.text:
        app.logger.info(event)

    splitted = event.message.text.split()
    if '!도움' in event.message.text:
        message = '*demoter_bot*\n\n' + \
            '*!도움* 도움말 보기\n' + \
            '*!등급* 당원 등급을 조회합니다\n' + \
            '*!빈도* 당원의 활동량을 조회합니다\n' + \
            '*!강등 @아이디 등급* 당원을 강등합니다\n' + \
            '*!승급 @아이디 등급* 당원을 승급합니다\n' + \
            '*!삭제 @아이디* 당원 등급을 삭제합니다' + \
            '*!명언* 오늘의 명언을 출력합니다'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))

    if splitted[0] == '!reset':
        r_entry = extract_entry(event)
        r.delete(r_entry)
        message = '리셋되었습니다'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))

    if splitted[0] == '!삭제':
        delete_entry(event)

    if splitted[0] in ('!빈도', '!частота'):
        show_frequency(event)

    if splitted[0] == '!강등':
        adjust_ranking('demote', event)

    if splitted[0] == '!승급':
        adjust_ranking('promote', event)

    if splitted[0] == '!등급':
        show_ranking(event)

    if splitted[0] == '!명언':
        show_today_message(event)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
