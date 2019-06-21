import random


def get_special_images(special: str) -> str:
    IMAGES = {
        'fumble': (
            # 'https://saveversus.files.wordpress.com/2014/09/missed.jpg',
            # 'https://i.kym-cdn.com/entries/icons/mobile/000/000/028/Fail-Stamp-Transparent_copy.jpg',
            # 'https://cgaseyer.files.wordpress.com/2011/12/epic-fail-demotivational-poster-1220242871.jpg',
            'http://file3.instiz.net/data/file3/2018/03/16/2/a/7/2a728ebac4f5292ca61cef0bc122b31d.gif',
            ),
        'critical': (
            'https://img.insight.co.kr/static/2017/05/22/700/21dj9r72yx01d4p9ii9x.jpg',
            'https://t1.daumcdn.net/cfile/tistory/223F70475298764C32',
            'https://cdn.pixabay.com/photo/2017/12/20/07/04/portrait-of-a-rock-kestrel-3029352_960_720.jpg',
            'https://image.fmkorea.com/files/attach/new/20170830/486616/751718523/760666026/e52694b85b51532def522fb9a667e8df.jpg',
            'https://opgg-com-image.akamaized.net/attach/images/20181121064523.641956.jpeg',
            ),
        }

    if special not in IMAGES:
        return ''

    return random.choice(IMAGES[special])

# flake8: noqa: E501
