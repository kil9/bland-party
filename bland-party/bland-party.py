import json
import random
import datetime
from collections import OrderedDict

from flask import request, abort
from pytz import timezone

from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,
)

from config import app, r, line_bot_api, handler
from utils import rreplace, get_score, moved_step_str
from help import help_message
from emoji import EMOJI_DICE, EMOJI_SMILE, EMOJI_SORRY, EMOJI_1ST, EMOJI_2ND, EMOJI_3RD
from emoji import EMOJI_ROBOT, EMOJI_BALANCE, EMOJI_HEART, EMOJI_BALLOON
from images import get_special_images


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
    app.logger.warn('deleting key: {}'.format(group_key))
    r.delete(group_key)

    return 'ok'


@app.route("/groups", methods=['DELETE'])
def reset_all_groups():
    app.logger.info('reset_all_groups request')
    for key in r.scan_iter(match=ENTRY_GROUP + '*', count=100):
        app.logger.info('deleting group_id: {}'.format(key))
        reset_group(key, is_key=True)

    return 'ok'


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


def ratings_to_message(ratings, target=None, old_rating=None, moved_steps=''):
    str = ''
    for person, rating in ratings.items():
        if person == target:
            str += '{} {} → {} {}\n'.format(person, old_rating, rating, moved_steps)
        else:
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


def roll(mod, dc, is_special=False):
    rolled = random.randint(1, 20)  # d20

    mod_str = ''
    if mod != 0:
        mod_str = ' ({0}{1:+d})'.format(rolled, mod)

    message = '{} {}{} vs. DC {}\n'.format(EMOJI_DICE, rolled+mod, mod_str, dc)

    if is_special:
        message += '자동성공입니다.'
        return True, message, ''

    if rolled >= 19 or rolled+mod == dc:
        message += '*크리티컬* 굴림에 성공했습니다.'
        return True, message, 'critical'

    if rolled == 1:
        message += '*펌블* 굴림에 실패했습니다.'
        return False, message, 'fumble'

    if rolled+mod >= dc:
        message += '굴림에 성공했습니다.'
    else:
        message += '굴림에 실패했습니다.'

    return rolled+mod >= dc, message, ''


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


def adjust_ranking(ratings, member_info, action, event, designated_target=None):
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

    if len(splitted) < 2:
        app.logger.warn('too short message to promote/demote')
        return

    if len(splitted) >= 3:
        target = splitted[1:-1]
        target = ' '.join(target)
        ranking_title = splitted[-1]

    if len(splitted) == 2:
        target = random.choice(tuple(ratings.keys()))
        ranking_title = splitted[-1]

    if target == '랜덤':
        target = random.choice(tuple(ratings.keys()))

    group_id, user_id = event.source.group_id, event.source.user_id
    if action == 'special_promote':
        profile = line_bot_api.get_group_member_profile(group_id, user_id)
        self_target = '@' + profile.display_name
        rank = list(ratings.keys()).index(self_target)
        if rank != 0:
            message_text = '랭킹 1위만 사면이 가능합니다'
            text_message = TextSendMessage(text=message_text)
            messages = [text_message]
            line_bot_api.reply_message(event.reply_token, messages)
            return

    if designated_target is not None:
        try:
            target = tuple(ratings.keys())[designated_target]
        except ValueError as e:
            app.logger.error(e)
            target = random.choice(tuple(ratings.keys()))

    try:
        rank = list(ratings.keys()).index(target)
    except ValueError as e:
        app.logger.error(e)
        rank = 10
    mod = calculate_mod(member_info, user_id)

    message = ''
    special = ''
    old_rating = ''
    moved_steps = ''
    if action in ('demote', 'super_demote'):
        if action == 'super_demote':
            success, message, special = roll(mod, max(1, 13-rank+5))
        else:
            success, message, special = roll(mod, max(1, 13-rank))

        if not success:
            profile = line_bot_api.get_group_member_profile(group_id, user_id)
            target = '@' + profile.display_name

        if target in ratings:
            old_rating = ratings[target]
        ratings[target] = ranking_title

        idx = list(ratings.keys()).index(target)
        move_index = min(idx + 1, len(ratings)-1)
        if special in ('critical', 'fumble') or action == 'super_demote':
            move_index = len(ratings)-1

        moved_steps = moved_step_str(idx, move_index)

        rating_list = list(ratings.items())
        target_item = rating_list[idx]
        rating_list = rating_list[:idx] + rating_list[idx+1:]
        rating_list.insert(move_index, target_item)
        ratings.clear()
        for k, v in rating_list:
            ratings[k] = v

    if action in ('promote', 'special_promote'):
        success, message, special = roll(mod, max(1, 13-rank), action == 'special_promote')

        if not success:
            profile = line_bot_api.get_group_member_profile(group_id, user_id)
            target = '@' + profile.display_name

        if target in ratings:
            old_rating = ratings[target]
        ratings[target] = ranking_title

        idx = list(ratings.keys()).index(target)
        move_index = max(idx - 1, 0)
        if special == 'critical':
            move_index = 0
        if not success:
            move_index = min(idx + 1, len(ratings)-1)

        moved_steps = moved_step_str(idx, move_index)

        rating_list = list(ratings.items())
        target_item = rating_list[idx]
        rating_list = rating_list[:idx] + rating_list[idx+1:]
        rating_list.insert(move_index, target_item)
        ratings.clear()
        for k, v in rating_list:
            ratings[k] = v

    message = ratings_to_message(ratings, target, old_rating, moved_steps) + '\n' + message
    text_message = TextSendMessage(text=message)
    messages = [text_message]
    if special in ('critical', 'fumble'):
        special_image = get_special_images(special)
        message = ImageSendMessage(
                original_content_url=special_image, preview_image_url=special_image)
        messages.append(message)

    try:
        line_bot_api.reply_message(event.reply_token, messages)
    except linebot.exceptions.LineBotApiError as e:
        app.logger.error(e)
        app.logger.error(f'image: {special_image}')


def show_ranking(ratings, event):
    message = ratings_to_message(ratings)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def predict_verdict(event):
    splitted = event.message.text.split()
    if len(splitted) < 2:
        app.logger.warn('too short message to verdict')
        return

    target = ' '.join(splitted[1:]).replace('@', '')
    verdicts = [
            '무죄', '징역 2년 집행유예 4년', '사형', '국종룸 24시간', '즉결처분',
            '징역 1년 집행유예 2년', '기소유예', '취업제한 5년', '기록 말소형',
            '120시간 사회봉사', '신상공개 10년', '칭호 박탈', '15일 구류',
            '훈방', '징역 30년', '징역 10년', '징벌적 손해배상 1억 5천만원',
            '무기징역', '무죄', '징역 1년', '벌금 300만원', '징역 40년']
    verdict = random.choice(verdicts)
    message = '{0} *AI 형량 예측 결과*\n'.format(EMOJI_BALANCE) + \
        f'{target}: {verdict}'
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def check_imposter(event):
    splitted = event.message.text.split()
    if len(splitted) < 2:
        app.logger.warn('too short message to check imposter')
        return
    target = ' '.join(splitted[1:]).replace('@', '')

    if random.randint(0, 3) == 0:
        imposter_message = '임포스터였습니다'
    else:
        imposter_message = '임포스터가 아니었습니다'

    message = '. 　。　　　　•　 　ﾟ　　。\n' + \
              '.　　 。　 ඞ 。　 . •\n' + \
              f'• {target} 는 {imposter_message}. 　 。　.\n' + \
              '　 　　。　　　　　　.　　　.　　　　　.\n'
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def show_today_message(member_info, event):
    filtered = filter(lambda x: 'message_today' in x[1], list(member_info.items()))

    user_id, user_info = random.choice(list(filtered))
    group_id = event.source.group_id
    profile = line_bot_api.get_group_member_profile(group_id, user_id)
    message = '*오늘의 명언*\n\n'
    message += '{}: {}'.format(profile.display_name, user_info['message_today'])
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def roll_dice(event):
    last_word = event.message.text.split()[-1]
    splitted = last_word.split('d')
    if len(splitted) == 1:
        x = 1
        y = splitted[0]
    else:
        x, y = last_word.split('d')

    if y == '%':
        y = 100

    rolls = []
    for i in range(int(x)):
        rolls.append(random.randint(1, int(y)))

    total = sum(rolls)
    total_string = ' '.join((str(r) for r in rolls))
    message = '결과: {} ({})'.format(total, total_string)

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


def do_versus(event):
    splitted = event.message.text.split(' vs. ')
    if len(splitted) < 2:
        return

    ranked = ((word, get_score(word.strip())) for word in splitted)
    rank_sorted = sorted(ranked, key=lambda m: m[1], reverse=True)

    message = ''
    for i, (word, score) in enumerate(rank_sorted):
        winner = '' if i > 0 else ' (winner)'
        message += '{}. {} ({}){}\n'.format(i+1, word, score, winner)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))


def detect_duplicates(member_info, event):
    splits = event.message.text.split(' ')
    for split in splits:
        if split.startswith('http'):
            link = split
            break
    else:
        return False

    group_id, user_id = event.source.group_id, event.source.user_id
    rkey = '{}_{}'.format(group_id, link)

    entry_serialized = r.get(rkey)
    if entry_serialized is not None:
        entry = json.loads(entry_serialized)

        message = '{} 삐빅 중복입니다\nby {} ({})'.format(
                EMOJI_ROBOT, entry['uploader'], entry['time'])
        messages = [TextSendMessage(text=message)]
        line_bot_api.reply_message(event.reply_token, messages)
        return True

    profile = line_bot_api.get_group_member_profile(group_id, user_id)
    uploader = '@' + profile.display_name

    KST = timezone('Asia/Seoul')
    d = datetime.datetime.now(tz=KST)
    entry = {
        'uploader': uploader,
        'time': d.strftime('%m/%d %H:%M'), }

    entry_serialized = json.dumps(entry)
    r.setex(rkey, 86400*3, entry_serialized)
    return False


def process_link(member_info, event):
    detect_duplicates(member_info, event)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.source.type != 'group':
        return

    member_info, ratings_info = load_group_info(event)

    message_preprocess(member_info, event)

    app.logger.info(f"group: {event.source.group_id}, text: {event.message.text}")

    if '!도움' in event.message.text:
        message = help_message(event.message.text)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=message))
        return

    if ' vs. ' in event.message.text:
        do_versus(event)
        return

    demote_commands = (
        '!강등',
        '!불매', '!понижение', '!降等', '!降格', '!こうとう',
        '!저격', '!낙선', '!낙천', '!세무조사',
        '!기소', '!고소', '!하하하', '!멈춰')

    frequency_commands = ('!빈도', '!частота', '!頻度', '!ひんど')

    splitted = event.message.text.split()
    if splitted[0] == '!삭제':
        delete_entry(ratings_info, event)
    elif splitted[0] in frequency_commands:
        show_frequency(member_info, event)
    elif splitted[0] in demote_commands:
        adjust_ranking(ratings_info, member_info, 'demote', event)
    elif splitted[0] == '!탄핵':
        adjust_ranking(ratings_info, member_info, 'demote', event, 0)
    elif splitted[0] == '!초강등':
        adjust_ranking(ratings_info, member_info, 'super_demote', event)
    elif splitted[0] in ('!승급', '!공천'):
        adjust_ranking(ratings_info, member_info, 'promote', event)
    elif splitted[0] in ('!사면', '!특사'):
        adjust_ranking(ratings_info, member_info, 'special_promote', event)
    elif splitted[0] in ('!등급', '!ранг'):
        show_ranking(ratings_info, event)
    elif splitted[0] in ('!명언', '!망언', '!пословица'):
        show_today_message(member_info, event)
    elif splitted[0] in ('!형량예측', '!형량', '!항소', '!상고'):
        predict_verdict(event)
    elif splitted[0] == '!임포스터':
        check_imposter(event)
    elif splitted[0] == '!roll':
        roll_dice(event)
    elif 'http' in event.message.text:
        process_link(member_info, event)
    elif event.message.text.startswith('힝') or event.message.text.endswith('힝'):
        text_message = TextSendMessage(text='어른스럽게 말해야지')
        messages = [text_message]
        line_bot_api.reply_message(event.reply_token, messages)

    save_group_info(member_info, ratings_info, event)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
