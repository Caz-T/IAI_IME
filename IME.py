import json
import math
import time
from pathlib import Path
from typing import Optional

begin_mark = '^^^'
void_mark = '???'


def opr(filename: str, suffix: str = 'txt'):
    return open(filename + '.' + suffix, mode='r', encoding='utf-8')


def opw(filename: str, suffix: str = 'txt'):
    return open(filename + '.' + suffix, mode='w', encoding='utf-8')


def get_max_from_dict(d: dict):
    return max(d, key=d.get)


def probe_pinyin(curr_str: str, pinyin: list, index: int, nd: dict, prev_key: str, loss: float, temp_best: dict):
    if loss > temp_best['loss']:
        return True
    if len(pinyin) == index:
        temp_best['loss'] = loss
        temp_best['str'] = curr_str
        print(temp_best)
        input()
        return True

    to_check = nd.get(prev_key, nd[void_mark]).get(pinyin[index], nd[void_mark][pinyin[index]])
    for (char, char_loss) in to_check:
        if probe_pinyin(curr_str + char, pinyin, index + 1, nd, char, loss + char_loss, temp_best):
            return False

    return True


def parse_pinyin_by_2gram(pinyin: str, ngram_dict: dict):
    pinyin = pinyin.split()
    if len(pinyin) == 0:
        return ''
    best_info = {'loss': math.inf, 'str': ''}
    print(pinyin)
    probe_pinyin('', pinyin, 0, ngram_dict, begin_mark, 0.0, best_info)
    return best_info['str']


def demo():
    with opr("weibo", "json") as fi:
        ngram_dict = json.load(fi)
    print("loaded")
    while True:
        st = input()
        st = st.strip()
        print(parse_pinyin_by_2gram(st, ngram_dict))





if __name__ == '__main__':
    with opr("weibo", 'json') as fi:
        ngram_dict = json.load(fi)
    validate(lambda pyl: parse_pinyin_by_2gram(pyl, ngram_dict), Path('.') / "my_output")
