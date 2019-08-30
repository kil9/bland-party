def help_message(message):
    if '!도움 등급' in message:
        return '*!등급* 명령으로 현재 등급을 조회합니다\n' + \
            '현재 등급이 높을수록 강등되기 어렵습니다.'
    if '!도움 빈도' in message:
        return '*!빈도* 명령으로 메시지 빈도를 조회합니다\n' + \
            '메시지 비율이 높을수록 강등당할 확률이 낮아지며,' + \
            '순위가 높으면 판정에 보너스를 받습니다.'
    if '!도움 강등' in message:
        return '*!강등 @아이디 등급* 명령으로\n' + \
            '특정 당원을 강등시킬 수 있습니다\n' + \
            '목표 DC를 대상으로 굴림에 실패할 경우 명령한 당원이 강등됩니다.'
    if '!도움 초강등' in message:
        return '*!초강등 @아이디 등급* 명령으로\n' + \
            '특정 당원을 초강등시킬 수 있습니다\n' + \
            'DC가 5 오르지만 성공할 경우 최하 등급으로 강등됩니다.'
    if '!도움 명언' in message:
        return '*!명언* 명령으로 오늘의 명언을 출력합니다\n' + \
            '몇 가지 의문의 알고리즘이 사용됩니다.'

    return '*demoter_bot*\n\n' + \
        '*!도움* 도움말 보기\n' + \
        '*!등급* 당원 등급을 조회합니다\n' + \
        '*!빈도* 당원의 활동량을 조회합니다\n' + \
        '*!강등 @아이디 등급* 당원을 강등합니다\n' + \
        '*!초강등 @아이디 등급* 당원을 초강등합니다\n' + \
        '*!승급 @아이디 등급* 당원을 승급합니다\n' + \
        '*!삭제 @아이디* 당원 등급을 삭제합니다\n' + \
        '*!명언* 오늘의 명언을 출력합니다'
