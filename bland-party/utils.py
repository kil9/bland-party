import json

from collections import OrderedDict

from config import app, r


def rreplace(s, old, new, occurrence):
    li = s.rsplit(old, occurrence)
    return new.join(li)


def load_ordered_dict(key):
    try:
        value_txt = r.get(key)
        ordered_dict = json.loads(value_txt, object_pairs_hook=OrderedDict)
    except Exception as e:
        app.logger.exception(e)
        ordered_dict = OrderedDict()

    return ordered_dict
