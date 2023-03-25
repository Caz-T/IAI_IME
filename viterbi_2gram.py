import json
import time
from pathlib import Path
from math import log
from typing import Optional

begin_mark = '^'


def get_ngram_freq(corpus: list[str], pinyin_dict: dict, verbose: bool = True):
    gram_dict = {}
    freq_dict = {}

    accepted_chars = set([char for group in pinyin_dict.values() for char in group])

    count = 0
    t = time.time()
    for sent in corpus:
        sent = sent.strip()
        count += 1
        if count % 10000 == 0:
            newt = time.time()
            if verbose:
                print("%d / %d sentences parsed in %d seconds" % (count, len(corpus), newt - t))
        if len(sent) == 0:
            continue
        segments = []
        curr_seg = begin_mark
        for i in range(len(sent)):
            if sent[i] not in accepted_chars:
                if len(curr_seg):
                    segments.append(curr_seg)
                    curr_seg = ''
                continue
            curr_seg += sent[i]
        if len(curr_seg):
            segments.append(curr_seg)
        for seg in segments:
            if len(seg) == 0:
                continue
            freq_dict[seg[0]] = freq_dict.get(seg[0], 0) + 1
            for i in range(len(seg) - 1):
                freq_dict[seg[i + 1]] = freq_dict.get(seg[i + 1], 0) + 1
                if seg[i] not in gram_dict:
                    gram_dict[seg[i]] = {}
                gram_dict[seg[i]][seg[i + 1]] = gram_dict[seg[i]].get(seg[i + 1], 0) + 1

    return freq_dict, gram_dict


def compute_prob(freq_dict: dict, gram_dict: dict, pinyin_dict: dict, smoothing_factor: float, verbose: bool = True):
    if verbose:
        print("start computing")
    prob_dict = {}
    total_freq = sum(freq_dict.values())
    accepted_chars = set([char for group in pinyin_dict.values() for char in group])
    char_count = len(accepted_chars)

    for c in accepted_chars:
        # if a character is not present in the corpus
        # we set its frequency to 1 to avoid math error
        freq_dict[c] = freq_dict.get(c, 1) / total_freq

    for prev_char in accepted_chars:
        prob_dict[prev_char] = {}
        if prev_char not in gram_dict:
            # if the previous character is not present in the corpus
            # we use frequency on the whole corpus instead
            for c in accepted_chars:
                prob_dict[prev_char][c] = log(char_count)
        else:
            total = sum(gram_dict[prev_char].values())
            for c in accepted_chars:
                prob_dict[prev_char][c] = - log(
                    smoothing_factor * gram_dict[prev_char].get(c, 0) / total +
                    (1 - smoothing_factor) * freq_dict[c]
                )
    prob_dict[begin_mark] = {}
    total = sum(gram_dict[begin_mark].values())
    for c in accepted_chars:
        prob_dict[begin_mark][c] = - log(
            smoothing_factor * gram_dict[begin_mark].get(c, 0) / total +
            (1 - smoothing_factor) * freq_dict[c]
        )

    return prob_dict


def get_prob_dict_core(corpus: list[str], pinyin_dict: dict, smoothing_factor: float = 0.2, verbose: bool = True):
    freq_dict, gram_dict = get_ngram_freq(corpus, pinyin_dict, verbose)
    prob_dict = compute_prob(freq_dict, gram_dict, pinyin_dict, smoothing_factor, verbose)
    return prob_dict


def get_prob_dict(corpus_file: Path, pinyin_file: Path, output_file: Path, smoothing_factor: float = 0.2):
    with corpus_file.open(mode='r', encoding='utf-8') as fi:
        corpus = [line.strip().replace(begin_mark, '') for line in fi.readlines()]
    with pinyin_file.open(mode='r', encoding='utf-8') as fi:
        pinyin_dict = json.load(fi)
    print("loaded!")

    prob_dict = get_prob_dict_core(corpus, pinyin_dict, smoothing_factor)

    print("start printing")
    with output_file.open(mode='w', encoding='utf-8') as fo:
        json.dump(prob_dict, fo)


def viterbi_2gram(pinyin: list[str], prob_dict: dict, pinyin_dict: dict):
    # Each entry in a layer is of form (min_loss, prefix_str).
    # Both store what you would expect them to.
    prev_layer = {begin_mark: (0, '')}
    curr_layer = {}
    for syl in pinyin:
        if syl not in pinyin_dict:
            # panic: output an underscore and restart the sentence
            prev_best = min(prev_layer.values(), key=lambda t: t[0])
            curr_layer = {begin_mark: (prev_best[0], prev_best[1] + '_')}
        else:
            for char in pinyin_dict[syl]:
                prev_best_k = min(prev_layer, key=lambda k: prev_layer[k][0] + prob_dict[k][char])
                curr_layer[char] = (prev_layer[prev_best_k][0] + prob_dict[prev_best_k][char],
                                    prev_layer[prev_best_k][1] + char)
        prev_layer = curr_layer
        curr_layer = {}

    return prev_layer[min(prev_layer, key=lambda k: prev_layer[k][0])][1]


def demo():
    print(time.time())
    with open('weibo.json', mode='r', encoding='utf-8') as fi:
        prob_dict = json.load(fi)
    print(time.time())
    with open('pinyin_to_hanzi.json', mode='r', encoding='utf-8') as fi:
        pinyin_dict = json.load(fi)
    print(time.time())

    while True:
        py = input()
        py = py.strip().split()
        print(viterbi_2gram(py, prob_dict, pinyin_dict))


def validate(predict_function, output: Optional[Path] = None, verbose: bool = True):
    with open('validation/input.txt', mode='r', encoding='utf-8') as fi:
        valid_set = [line.strip() for line in fi]
    with open('validation/std_output.txt', mode='r', encoding='utf-8') as fi:
        std_output = [line.strip() for line in fi]

    if verbose:
        print(len(valid_set))
    t0 = time.time()
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
    elapsed = time.time() - t0

    if fout is not None:
        fout.close()
    if verbose:
        print("By character: %d / %d, accuracy %.4f" % (corr_char, char_count, corr_char / char_count))
        print("By sentence: %d / %d, accuracy %.4f" % (corr_sent, len(valid_set), corr_sent / len(valid_set)))
        print("Validation time: %d secs, avg %.2f sentences per second" % (int(elapsed), len(valid_set) / elapsed))
    return corr_char / char_count, corr_sent / len(valid_set)


def auto_learn(corpus: list[str], pinyin_dict: dict, init_fa: float = 0.5, init_step: float = 0.5):
    fa = init_fa
    step = init_step
    pd = get_prob_dict_core(corpus, pinyin_dict, fa, False)
    c, _ = validate(lambda t: viterbi_2gram(t.strip().split(), pd, pinyin_dict), None, False)


def train_and_test_sina_news(fa: float):
    corpus = Path('corpus/sina_news.txt').open(mode='r', encoding='utf-8').readlines()
    pinyin_dict = json.load(Path('pinyin_to_hanzi.json').open(mode='r', encoding='utf-8'))
    prob_dict = get_prob_dict_core(corpus, pinyin_dict, fa, True)
    with open('pinyin_to_hanzi.json', mode='r', encoding='utf-8') as fi:
        pinyin_dict = json.load(fi)
    validate(lambda t: viterbi_2gram(t.strip().split(), prob_dict, pinyin_dict), Path("my_output.txt"))


def train_sina_news(fa: float):
    get_prob_dict(Path('corpus/sina_news.txt'), Path('pinyin_to_hanzi.json'), Path('sina_news-%.4f.json' % fa), fa)


if __name__ == '__main__':
    pass


