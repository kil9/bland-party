import random


def get_special_images(special: str) -> str:
    IMAGES = {
        'fumble': (
            'https://saveversus.files.wordpress.com/2014/09/missed.jpg',
            'https://i.kym-cdn.com/entries/icons/mobile/000/000/028/Fail-Stamp-Transparent_copy.jpg',  # noqa: E501
            ),
        'critical': (
            'https://img.insight.co.kr/static/2017/05/22/700/21dj9r72yx01d4p9ii9x.jpg',
            'https://t1.daumcdn.net/cfile/tistory/223F70475298764C32',
            ),
        }

    if special not in IMAGES:
        return ''

    return random.choice(IMAGES[special])
