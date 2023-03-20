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


def load_ngram_by_char(sents: list, gram_count: int, d: dict, pinyin_dict: dict):
    print("total: %d sentences" % len(sents))
    count = 0
    t = time.time()
    if begin_mark not in d:
        d[begin_mark] = {}
    if void_mark not in d:
        d[void_mark] = {}

    for sent in sents:
        if len(sent) == 0:
            continue
        if sent[0] in pinyin_dict:
            first_syllable = pinyin_dict[sent[0]]
            if first_syllable not in d[begin_mark]:
                d[begin_mark][first_syllable] = {}
            d[begin_mark][first_syllable][sent[0]] = d[begin_mark][first_syllable].get(sent[0], 0) + 1
            if first_syllable not in d[void_mark]:
                d[void_mark][first_syllable] = {}
            d[void_mark][first_syllable][sent[0]] = d[void_mark][first_syllable].get(sent[0], 0) + 1

        for i in range(len(sent) - gram_count + 1):
            if not all([(char in pinyin_dict) for char in sent[i: i + gram_count]]):
                continue
            key = sent[i: i + gram_count - 1]
            if key not in d:
                d[key] = {}
            last_syllable = pinyin_dict[sent[i + gram_count - 1]]
            if last_syllable not in d[key]:
                d[key][last_syllable] = {}
            if last_syllable not in d[void_mark]:
                d[void_mark][last_syllable] = {}
            d[key][last_syllable][sent[i + gram_count - 1]] = d[key][last_syllable].get(sent[i + gram_count - 1], 0) + 1
            d[void_mark][last_syllable][sent[i + gram_count - 1]] = \
                d[void_mark][last_syllable].get(sent[i + gram_count - 1], 0) + 1
        count += 1
        if count % 10000 == 0:
            newt = time.time()
            print("%d sentences parsed in %d seconds" % (count, newt - t))


def load_char_freq(sents: list, d: dict, pinyin_dict: dict):
    for sent in sents:
        for char in sent:
            if char not in pinyin_dict:
                continue
            if pinyin_dict[char] not in d:
                d[pinyin_dict[char]] = {}
            d[pinyin_dict[char]][char] = d[pinyin_dict[char]].get(char, 0) + 1


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


def get_ngram(corpus_file: Path, pinyin_file: Path, output_file: Path):
    d = {}
    with corpus_file.open(mode='r', encoding='utf-8') as fi:
        corpus = [line.strip() for line in fi.readlines()]
    with pinyin_file.open(mode='r', encoding='utf-8') as fi:
        pinyin_dict = json.load(fi)
    print("loaded!")

    t0 = time.time()
    load_ngram_by_char(corpus, 2, d, pinyin_dict)
    t1 = time.time()
    print("load 2gram: %d secs" % int(t1 - t0))
    with output_file.open(mode='w', encoding='utf-8') as fo:
        json.dump(d, fo)
    t2 = time.time()
    print("write to disk: %d secs" % int(t2 - t1))


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
    # get_ngram(Path("/Users/casorazitora/Desktop/Learn new stuff/大二下/人智导/输入法作业/语料库/sina_news.txt"),
              # Path("course_pinyin_dict.json"), Path("sina_news.json"))
    with opr("sina_news", 'json') as fi:
        ngram_dict = json.load(fi)

    validate(lambda pyl: parse_pinyin_by_ngram(pyl, ngram_dict), Path('.') / "my_output")