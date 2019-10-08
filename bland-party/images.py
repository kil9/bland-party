import random


def get_special_images(special: str) -> str:
    IMAGES = {
        'fumble': (
            'https://pbs.twimg.com/media/DnbsBXgVAAEElMT.jpg',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQX9WrbDwJ8p24u5HsnOmxJMSKac2KnWVPTmvWQzG_fXoN52pID',
            'https://mblogthumb-phinf.pstatic.net/MjAxODA1MjRfMjAy/MDAxNTI3MTQ3MzQwMjg0.HZ_q7z0I7ojg0tyrNGk5iu73BNRPraR2xD6UOmYXH_Eg.Afw1a3P8cXsKXnnYjIdBYFqDELJ6RpHJuNu9Eafj_Ikg.JPEG.vvso2vv/1527147320273.jpg?type=w800',
            'https://pbs.twimg.com/media/ECfvK_cU0AERZsO?format=jpg&name=large',
            'https://cdn.clien.net/web/api/file/F01/4346589/301a6a44b7e246fc922.JPG',
            'https://pbs.twimg.com/media/EBhxMOnUYAAOo-g?format=jpg&name=small',
            'https://ext.fmkorea.com/files/attach/new/20180612/486616/1098240456/1101149921/8d45b0576f7c1c8a7bd7f2f2d54b8699.jpg',
            'https://postfiles.pstatic.net/MjAxOTA1MTJfOTMg/MDAxNTU3NjY3MzM3NjI1.BzDjh7Mv8jmeL3sv-9GrJtpJ-Cl8EumNTCNR078s_SAg.87z2pokBaaH5lkidxAwibvjBiBTFM-I88jbilTtRGEQg.JPEG.jjyynr/2.jpg?type=w773',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTy2lCnqvYnPvjOp1Y0w1ABDdSchcKB0arqA8yRC1NAQUk_jKHs',
            'http://cfs5.tistory.com/upload_control/download.blog?fhandle=YmxvZzEyNDc4OUBmczUudGlzdG9yeS5jb206L2F0dGFjaC8wLzAxMDAwMDAwMDA1Ni5qcGc%3D',
            ),
        'critical': (
            # 'https://img.insight.co.kr/static/2017/05/22/700/21dj9r72yx01d4p9ii9x.jpg',
            # 'https://image.fmkorea.com/files/attach/new/20180609/486616/848139831/1095267532/3020853034a1b9c9180cab842acfd742.JPEG',
            # 'https://pbs.twimg.com/media/DQYKxpsV4AE2QXv.jpg',
            # 'https://pbs.twimg.com/media/EDiDW6FUUAAN2X2?format=jpg&name=large',
            'https://pbs.twimg.com/media/C_3kSnxVwAAqf2Q?format=jpg&name=large',
            'https://opgg-com-image.akamaized.net/attach/images/20190616133629.752528.jpeg',
            'https://i.pinimg.com/564x/c3/85/9b/c3859bc750bffe194e0bf912d234df53.jpg',
            'https://i.imgur.com/SpM5Chv.jpg',
            'https://i.pinimg.com/originals/a8/ab/b0/a8abb07aabf631065f727821f9eb81a4.jpg',
            'https://image.fmkorea.com/files/attach/new/20180908/486616/944884088/1256967785/c1384c8976b775eddb246cc2f82082ff.png',
            ),
        }

    if special not in IMAGES:
        return ''

    return random.choice(IMAGES[special])

# flake8: noqa: E501
