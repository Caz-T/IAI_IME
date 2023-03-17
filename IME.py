import json
import time


def opr(filename: str, suffix: str = 'txt'):
    return open(filename + '.' + suffix, mode='r', encoding='utf-8')


def opw(filename: str, suffix: str = 'txt'):
    return open(filename + '.' + suffix, mode='w', encoding='utf-8')


def load_ngram_by_char(sents: list, gram_count: int, d: dict, pinyin_dict: dict):
    print("total: %d sentences" % len(sents))
    count = 0
    t = time.time()
    for sent in sents:
        if len(sent) == 0:
            continue
        if sent[0] in pinyin_dict:
            if '^^^' not in d:
                d['^^^'] = {}
            first_syllable = pinyin_dict[sent[0]]
            if first_syllable not in d['^^^']:
                d['^^^'][first_syllable] = {}
            d['^^^'][first_syllable][sent[0]] = d['^^^'][first_syllable].get(sent[0], 0) + 1

        for i in range(len(sent) - gram_count + 1):
            if not all([(char in pinyin_dict) for char in sent[i: i + gram_count]]):
                continue
            key = sent[i: i + gram_count - 1]
            if key not in d:
                d[key] = {}
            last_syllable = pinyin_dict[sent[i + gram_count - 1]]
            if last_syllable not in d[key]:
                d[key][last_syllable] = {}
            d[key][last_syllable][sent[i + gram_count - 1]] = d[key][last_syllable].get(sent[i + gram_count - 1], 0) + 1
        count += 1
        if count % 10000 == 0:
            newt = time.time()
            print("%d sentences parsed with %d seconds" % (count, newt - t))


if __name__ == '__main__':
    d = {}
    with opr('/Users/casorazitora/Desktop/Learn new stuff/大二下/人智导/输入法作业/语料库/weibo') as fi:
        corpus = [line.strip() for line in fi.readlines()]
    with opr('/Users/casorazitora/Desktop/Learn new stuff/大二下/人智导/输入法作业/拼音汉字表/course_pinyin_dict', 'json') as fi:
        pinyin_dict = json.load(fi)
    print("loaded!")

    t0 = time.time()
    load_ngram_by_char(corpus, 2, d, pinyin_dict)
    t1 = time.time()
    print("load 2gram: %d secs" % int(t1 - t0))
    with opw('2gram_weibo', 'json') as fo:
        json.dump(d, fo)
    t2 = time.time()
    print("write to disk: %d secs" % int(t2 - t1))


