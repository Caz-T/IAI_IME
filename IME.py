import json
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


def parse_pinyin_by_ngram(pinyin: str, ngram_dict: dict):
    syllables = pinyin.split()
    if len(syllables) == 0:
        return ''
    if len(syllables) == 1:
        try:
            return get_max_from_dict(ngram_dict[begin_mark][syllables[0]])
        except KeyError:
            try:
                return get_max_from_dict(ngram_dict[void_mark][syllables[0]])
            except KeyError:
                return '一'
    try:
        answers = [get_max_from_dict(ngram_dict[begin_mark][syllables[0]]), ]
    except KeyError:
        try:
            answers = [get_max_from_dict(ngram_dict[void_mark][syllables[0]]), ]
        except KeyError:
            answers = ['一', ]
    for syl in syllables[1:]:
        try:
            answers.append(get_max_from_dict(ngram_dict[answers[-1]][syl]))
        except KeyError:
            try:
                answers.append(get_max_from_dict(ngram_dict[void_mark][syl]))
            except KeyError:
                answers.append('一')
    return "".join(answers)


def demo():
    with opr("2gram_sina", "json") as fi:
        ngram_dict = json.load(fi)
    with opr("word_freq_sina", "json") as fi:
        freq_dict = json.load(fi)
    print("loaded")
    while True:
        st = input()
        st = st.strip()
        print(parse_pinyin_by_ngram(st, ngram_dict))


def validate(predict_function, output: Optional[Path] = None):
    with opr('validation/input') as fi:
        valid_set = [line.strip() for line in fi]
    with opr('validation/std_output') as fi:
        std_output = [line.strip() for line in fi]

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
    with opr("sina_news", 'json') as fi:
        ngram_dict = json.load(fi)
    validate(lambda pyl: parse_pinyin_by_ngram(pyl, ngram_dict), Path('.') / "my_output")