import random


def get_special_images(special: str) -> str:
    IMAGES = {
        'fumble': (
            'https://mblogthumb-phinf.pstatic.net/MjAxODA1MjRfMjAy/MDAxNTI3MTQ3MzQwMjg0.HZ_q7z0I7ojg0tyrNGk5iu73BNRPraR2xD6UOmYXH_Eg.Afw1a3P8cXsKXnnYjIdBYFqDELJ6RpHJuNu9Eafj_Ikg.JPEG.vvso2vv/1527147320273.jpg?type=w800',
            'https://cdn.clien.net/web/api/file/F01/4346589/301a6a44b7e246fc922.JPG',
            'https://ext.fmkorea.com/files/attach/new/20180612/486616/1098240456/1101149921/8d45b0576f7c1c8a7bd7f2f2d54b8699.jpg',
            'https://postfiles.pstatic.net/MjAxOTA1MTJfOTMg/MDAxNTU3NjY3MzM3NjI1.BzDjh7Mv8jmeL3sv-9GrJtpJ-Cl8EumNTCNR078s_SAg.87z2pokBaaH5lkidxAwibvjBiBTFM-I88jbilTtRGEQg.JPEG.jjyynr/2.jpg?type=w773',
            'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTy2lCnqvYnPvjOp1Y0w1ABDdSchcKB0arqA8yRC1NAQUk_jKHs',
            'http://cfs5.tistory.com/upload_control/download.blog?fhandle=YmxvZzEyNDc4OUBmczUudGlzdG9yeS5jb206L2F0dGFjaC8wLzAxMDAwMDAwMDA1Ni5qcGc%3D',
            ),
        'critical': (
            # 'https://i.pinimg.com/564x/c3/85/9b/c3859bc750bffe194e0bf912d234df53.jpg', # ride check
            # 'https://i.imgur.com/SpM5Chv.jpg', # bluff
            # 'https://i.pinimg.com/originals/a8/ab/b0/a8abb07aabf631065f727821f9eb81a4.jpg', # luck
            # 'https://www.dogdrip.net/dvs/c/20/01/12/282ced159f23c8ee93a25fa0b37f2f52.jpg',
            'https://i2.ruliweb.com/ori/19/09/14/16d2e7f2a1f4ef6d2.jpg',
            'https://opgg-com-image.akamaized.net/attach/images/20190616133629.752528.jpeg',
            'https://image.fmkorea.com/files/attach/new/20180908/486616/944884088/1256967785/c1384c8976b775eddb246cc2f82082ff.png',
            'https://i1.ruliweb.com/img/19/12/05/16ed44590ad3623dd.jpg',
            'https://i3.ruliweb.com/ori/20/12/05/17632dc5aae533261.gif',
            'https://upload3.inven.co.kr/upload/2020/12/07/bbs/i013356575322.gif', # 당연히 말이 되죠
            ),
        }

    if special not in IMAGES:
        return ''

    return random.choice(IMAGES[special])

# flake8: noqa: E501
