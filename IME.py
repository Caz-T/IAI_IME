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


def validate(predict_function, output: Optional[Path] = None):
    with opr('validation/input') as fi:
        valid_set = [line.strip() for line in fi]
    with opr('validation/std_output') as fi:
        std_output = [line.strip() for line in fi]

    print(len(valid_set))
    char_count = sum([len(t) for t in std_output])
    corr_char = 0
    corr_sent = 0
    if output is not None:
        fout = output.open(mode='w', encoding='utf-8')
    else:
        fout = None

    for i in range(len(valid_set)):
        prediction = predict_function(valid_set[i])
        if fout is not None:
            print(prediction, file=fout)
            print(prediction)
        print(prediction)
        if len(prediction) != len(std_output[i]):
            continue
        flag = True
        for j in range(len(prediction)):
            if prediction[j] == std_output[i][j]:
                corr_char += 1
            else:
                flag = False
        if flag:
            corr_sent += 1

    if fout is not None:
        fout.close()
    print("By character: %d / %d, accuracy %.4f" % (corr_char, char_count, corr_char / char_count))
    print("By sentence: %d / %d, accuracy %.4f" % (corr_sent, len(valid_set), corr_sent / len(valid_set)))


if __name__ == '__main__':
    with opr("weibo", 'json') as fi:
        ngram_dict = json.load(fi)
    validate(lambda pyl: parse_pinyin_by_2gram(pyl, ngram_dict), Path('.') / "my_output")
