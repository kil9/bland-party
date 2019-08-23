import random


def get_special_images(special: str) -> str:
    IMAGES = {
        'fumble': (
            'https://pbs.twimg.com/media/DnbsBXgVAAEElMT.jpg',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQX9WrbDwJ8p24u5HsnOmxJMSKac2KnWVPTmvWQzG_fXoN52pID',
            'https://mblogthumb-phinf.pstatic.net/MjAxODA1MjRfMjAy/MDAxNTI3MTQ3MzQwMjg0.HZ_q7z0I7ojg0tyrNGk5iu73BNRPraR2xD6UOmYXH_Eg.Afw1a3P8cXsKXnnYjIdBYFqDELJ6RpHJuNu9Eafj_Ikg.JPEG.vvso2vv/1527147320273.jpg?type=w800',
            'https://pbs.twimg.com/media/ECfvK_cU0AERZsO?format=jpg&name=large',
            'https://cdn.clien.net/web/api/file/F01/4346589/301a6a44b7e246fc922.JPG',
            ),
        'critical': (
            'https://img.insight.co.kr/static/2017/05/22/700/21dj9r72yx01d4p9ii9x.jpg',
            'https://image.fmkorea.com/files/attach/new/20180609/486616/848139831/1095267532/3020853034a1b9c9180cab842acfd742.JPEG',
            'https://pbs.twimg.com/media/C_3kSnxVwAAqf2Q?format=jpg&name=large',
            ),
        }

    if special not in IMAGES:
        return ''

    return random.choice(IMAGES[special])

# flake8: noqa: E501
