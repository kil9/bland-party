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

from utils import rreplace

from help import help_message

from emoji import EMOJI_DICE, EMOJI_SMILE, EMOJI_SORRY, EMOJI_1ST, EMOJI_2ND, EMOJI_3RD


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


def delete_entry(ratings, event):
    splitted = event.message.text.split()
    if len(splitted) < 2:
        print('[WARN] too short message to demote')
        return

    to_delete = ' '.join(splitted[1:])
    if to_delete in ratings:
        del ratings[to_delete]
        message = '삭제되었습니다 {}'.format(EMOJI_SMILE)
    else:
        message = '삭제할 수 없습니다 {}'.format(EMOJI_SORRY)

    message = ratings_to_message(ratings) + '\n\n' + message
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def roll(mod, dc):
    rolled = random.randint(1, 20)  # d20

    mod_str = ''
    if mod != 0:
        mod_str = ' ({0}{1:+d})'.format(rolled, mod)

    message = '{} {}{} vs. DC {}\n'.format(EMOJI_DICE, rolled+mod, mod_str, dc)

    if rolled == 20:
        message += '*크리티컬* 굴림에 성공했습니다.'
        return True, message

    if rolled == 1:
        message += '*펌블* 굴림에 실패했습니다.'
        return False, message

    if rolled+mod >= dc:
        message += '굴림에 성공했습니다.'
    else:
        message += '굴림에 실패했습니다.'

    return rolled+mod >= dc, message


def do_calculate_mod(rank, length):
    if rank < 3:
        return 3 - rank
    if rank >= length-3:
        return 1 + 2 * (2 - (length-1 - rank))
    return 0


def calculate_mod(member_info, user_id):
    message_frequency = OrderedDict()
    for member_user_id, user_info in member_info.items():
        message_frequency[member_user_id] = user_info['n_message']

    sorted_users = sorted(message_frequency.items(), key=lambda m: m[1], reverse=True)

    try:
        freq_rank = list(u[0] for u in sorted_users).index(user_id)
    except ValueError:
        return 0

    mod = do_calculate_mod(freq_rank, len(member_info))
    return mod


def adjust_ranking(ratings, member_info, action, event):
    '''
    ** event example **
    {"message": {"id": "9760259091048", "text": "text text", "type": "text"},
     "replyToken": "4b35e226593e42a7ba0f53fd34b4a71b",
     "source": {"groupId": "C96673d1530d37de2b0a8ffc2e5df5f1f",
                "type": "group",
                "userId": "U13990d12ea3aa82eef9e01fcea9a963f"},
     "timestamp": 1556272465993, "type": "message"}
     '''

    splitted = event.message.text.split()

    if len(splitted) < 3:
        app.logger.warn('too short message to promote/demote')
        return

    if len(splitted) >= 3:
        target = splitted[1:-1]
        target = ' '.join(target)
        ranking_title = splitted[-1]

    message = ''
    if action == 'demote':
        group_id, user_id = event.source.group_id, event.source.user_id
        try:
            rank = list(ratings.keys()).index(target)
        except ValueError:
            rank = 10

        mod = calculate_mod(member_info, user_id)

        success, message = roll(mod, 13-rank)
        if not success:
            profile = line_bot_api.get_group_member_profile(group_id, user_id)
            target = '@' + profile.display_name

    if target in ratings:
        del ratings[target]

    ratings[target] = ranking_title
    if action == 'promote':
        ratings.move_to_end(target, last=False)

    message = ratings_to_message(ratings) + '\n' + message
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def show_ranking(ratings, event):
    message = ratings_to_message(ratings)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def show_today_message(member_info, event):
    filtered = filter(lambda x: 'message_today' in x[1], list(member_info.items()))

    user_id, user_info = random.choice(list(filtered))
    group_id = event.source.group_id
    profile = line_bot_api.get_group_member_profile(group_id, user_id)
    message = '*오늘의 명언*\n\n'
    message += '{}: {}'.format(profile.display_name, user_info['message_today'])
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def show_frequency(member_info, event):
    message_frequency = OrderedDict()
    for user_id, user_info in member_info.items():
        group_id = event.source.group_id
        profile = line_bot_api.get_group_member_profile(group_id, user_id)
        message_frequency[profile.display_name] = user_info['n_message']

    sorted_users = sorted(message_frequency.items(), key=lambda m: m[1], reverse=True)

    sum_messages = sum((m[1] for m in sorted_users))

    message = '*오늘의 메시지 수({})*\n\n'.format(sum_messages)
    for i, (user_name, frequency) in enumerate(sorted_users):
        medals = {0: EMOJI_1ST, 1: EMOJI_2ND, 2: EMOJI_3RD}

        mod = do_calculate_mod(i, len(member_info))
        mod_str = ''
        if mod > 0:
            mod_str = '/+{}'.format(mod)
        elif mod < 0:
            mod_str = '/{}'.format(mod)

        if i in medals:
            message += '{} '.format(medals[i])
        message += '{0}: {1}회 ({2:.1f}%{3})\n'.format(
                user_name, frequency, frequency/sum_messages*100.0, mod_str)

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


def message_preprocess(member_info, event):
    user_id = event.source.user_id
    message = event.message.text
    if user_id not in member_info:
        member_info[user_id] = {'n_message': 0, 'message_today': message}
    else:
        if has_to_change_message(member_info[user_id], message):
            member_info[user_id]['message_today'] = message

    member_info[user_id]['n_message'] += 1


def load_group_info(event):
    member_key = '{}_{}'.format(ENTRY_GROUP, event.source.group_id)
    ratings_key = '{}_{}'.format(ENTRY_RATINGS, event.source.group_id)

    member_info_raw, ratings_info_raw = r.mget(member_key, ratings_key)

    if member_info_raw is not None:
        member_info = json.loads(member_info_raw, object_pairs_hook=OrderedDict)
    else:
        member_info = OrderedDict()

    if ratings_info_raw is not None:
        ratings_info = json.loads(ratings_info_raw, object_pairs_hook=OrderedDict)
    else:
        ratings_info = OrderedDict()

    return member_info, ratings_info


def save_group_info(member_info, ratings_info, event):
    member_key = '{}_{}'.format(ENTRY_GROUP, event.source.group_id)
    ratings_key = '{}_{}'.format(ENTRY_RATINGS, event.source.group_id)

    member_info_serialized = json.dumps(member_info)
    r.setex(member_key, 86400, member_info_serialized)

    ratings_info_serialized = json.dumps(ratings_info)
    r.setex(ratings_key, 14*86400, ratings_info_serialized)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.source.type != 'group':
        return

    member_info, ratings_info = load_group_info(event)

    message_preprocess(member_info, event)

    if '!도움' in event.message.text:
        message = help_message(event.message.text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))
        return

    if event.message.text == '오오':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='해해'))
        return

    if event.message.text == '해해':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='성성'))
        return

    if '허..' in event.message.text:
        message = random.choice(('원..', '인..'))
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))
        return

    if event.message.text in ('원..', '인..'):
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='영..'))
        return

    splitted = event.message.text.split()
    if splitted[0] == '!삭제':
        delete_entry(ratings_info, event)
    elif splitted[0] in ('!빈도', '!частота'):
        show_frequency(member_info, event)
    elif splitted[0] == '!강등':
        adjust_ranking(ratings_info, member_info, 'demote', event)
    elif splitted[0] == '!승급':
        adjust_ranking(ratings_info, member_info, 'promote', event)
    elif splitted[0] == '!등급':
        show_ranking(ratings_info, event)
    elif splitted[0] == '!명언':
        show_today_message(member_info, event)

    save_group_info(member_info, ratings_info, event)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
