import json
import time
from pathlib import Path
from math import log

begin_mark = '^^^'
void_mark = '???'


def load_ngram_by_char(sents: list, gram_count: int, d: dict, freq_dict: dict, pinyin_dict: dict):
    print("total: %d sentences" % len(sents))
    count = 0
    t = time.time()
    if begin_mark not in d:
        d[begin_mark] = {}

    for sent in sents:
        if len(sent) == 0:
            continue
        if sent[0] in pinyin_dict:
            first_syllables = pinyin_dict[sent[0]]
            for first_syllable in first_syllables:
                if first_syllable not in d[begin_mark]:
                    d[begin_mark][first_syllable] = {}
                d[begin_mark][first_syllable][sent[0]] = d[begin_mark][first_syllable].get(sent[0], 0) + 1
                if first_syllable not in freq_dict:
                    freq_dict[first_syllable] = {}
                freq_dict[first_syllable][sent[0]] = freq_dict[first_syllable].get(sent[0], 0) + 1

        for i in range(len(sent) - gram_count + 1):
            if not all([(char in pinyin_dict) for char in sent[i: i + gram_count]]):
                continue
            key = sent[i: i + gram_count - 1]
            if key not in d:
                d[key] = {}
            last_syllables = pinyin_dict[sent[i + gram_count - 1]]
            for last_syllable in last_syllables:
                if last_syllable not in d[key]:
                    d[key][last_syllable] = {}
                if last_syllable not in freq_dict:
                    freq_dict[last_syllable] = {}
                d[key][last_syllable][sent[i + gram_count - 1]] = \
                    d[key][last_syllable].get(sent[i + gram_count - 1], 0) + 1
                freq_dict[last_syllable][sent[i + gram_count - 1]] = \
                    freq_dict[last_syllable].get(sent[i + gram_count - 1], 0) + 1
        count += 1
        if count % 10000 == 0:
            newt = time.time()
            print("%d sentences parsed in %d seconds" % (count, newt - t))


def compute_prob(ngram_dict: dict, freq_dict: dict, smoothing_factor: float = 0.2):
    for key in freq_dict:
        total = sum(freq_dict[key].values())
        for char in freq_dict[key]:
            freq_dict[key][char] = freq_dict[key][char] / total
    prob_dict = {}
    for key in ngram_dict:
        prob_dict[key] = {}
        for syl in ngram_dict[key]:
            temp_syl = {}
            total = sum(ngram_dict[key][syl].values())
            for char in ngram_dict[key][syl]:
                temp_syl[char] = \
                    - log(smoothing_factor * (ngram_dict[key][syl].get(char, 0) / total)
                          + (1 - smoothing_factor) * freq_dict[syl][char])
            prob_dict[key][syl] = [(k, temp_syl[k]) for k in temp_syl]
            prob_dict[key][syl].sort(key=lambda t: t[1])
    for key in freq_dict:
        freq_dict[key] = [(k, freq_dict[key][k]) for k in freq_dict[key]]
        freq_dict[key].sort(key=lambda t: t[1])
    prob_dict[void_mark] = freq_dict
    return prob_dict


def get_ngram(corpus_file: Path, pinyin_file: Path, output_file: Path):
    ngram_dict = {}
    freq_dict = {}
    with corpus_file.open(mode='r', encoding='utf-8') as fi:
        corpus = [line.strip() for line in fi.readlines()]
    with pinyin_file.open(mode='r', encoding='utf-8') as fi:
        pinyin_dict = json.load(fi)
    print("loaded!")

    t0 = time.time()
    load_ngram_by_char(corpus, 2, ngram_dict, freq_dict, pinyin_dict)
    t1 = time.time()
    print("load 2gram: %d secs" % int(t1 - t0))
    prob_dict = compute_prob(ngram_dict, freq_dict)
    t2 = time.time()
    print("compute prob: %d secs" % int(t2 - t1))
    with output_file.open(mode='w', encoding='utf-8') as fo:
        json.dump(prob_dict, fo)
    t3 = time.time()
    print("write to disk: %d secs" % int(t3 - t2))


if __name__ == '__main__':
    get_ngram(Path("/Users/casorazitora/Desktop/Learn new stuff/大二下/人智导/输入法作业/语料库/weibo.txt"),
              Path("mul_parsed.json"), Path("weibo.json"))
