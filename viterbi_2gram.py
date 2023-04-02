import json
import math
import time
from pathlib import Path
from math import log
from typing import Optional

from mydict import MyDict

begin_char = '^'
default_char = '#'


def wash_corpus(corpus: list[str], accepted_chars: set):
    print("Washing corpus")
    washed_corpus = []
    for sent in corpus:
        sent = sent.strip()
        segments = []
        curr_seg = ''
        for i in range(len(sent)):
            if sent[i] not in accepted_chars:
                if len(curr_seg):
                    segments.append(curr_seg)
                    curr_seg = ''
                continue
            curr_seg += sent[i]
        if len(curr_seg):
            segments.append(curr_seg)
        washed_corpus.append(segments)
    return washed_corpus


def get_freq(corpus: list[list[str]], base_dict: MyDict = None, verbose: bool = True):
    """
    Count frequency of every character in a corpus.

    :param corpus: segmented corpus. See `wash_corpus`.
    :param base_dict: previous freq dict if applicable. For accumulative training.
    :param verbose: provide verbose output or not.
    :return: a frequency dictionary, each key-value pair denoting one character. Characters not present in the corpus do not have an entry.
    """
    freq_dict = MyDict() if base_dict is None else base_dict

    for sent in corpus:
        for char in "".join(sent):
            freq_dict.incr(char)

    return freq_dict


def get_ngram(corpus: list[list[str]], gram_count: int, base_dict: MyDict = None, verbose: bool = True):
    """
    Count n-gram frequency of a given corpus.

    :param corpus: segmented corpus. See `wash_corpus`.
    :param gram_count: the parameter n as in n-gram.
    :param base_dict: previous gram dict if applicable. For accumulative training.
    :param verbose: provide verbose output or not.
    :return: an n-gram dictionary. Each key is a (n-1)-chars-long sector, and its value is a dict holding the frequency of all its successive parts. Patterns not present in the corpus do not have an entry.
    """
    gram_dict = MyDict() if base_dict is None else base_dict

    count = 0
    t = time.time()
    for sent in corpus:
        count += 1
        if count % 10000 == 0:
            newt = time.time()
            if verbose:
                print("%d / %d sentences parsed in %d seconds" % (count, len(corpus), newt - t))
        if len(sent) == 0:
            continue
        sent[0] = begin_char * (gram_count - 1) + sent[0]

        for seg in sent:
            if len(seg) < gram_count:
                continue
            for i in range(len(seg) - gram_count + 1):
                key = seg[i: i + gram_count - 1]
                if key not in gram_dict:
                    gram_dict[key] = MyDict()
                gram_dict[key].incr(seg[i + gram_count - 1])

    return gram_dict


def compute_loss(freq_dict: dict, gram_dict: dict, accepted_chars: set, smoothing_factor: float, verbose: bool = True):
    """
    Compute the probabilistic loss of each n-gram pattern. Loss is defined as -log(p) where p = μ * ngram_prob + (1 - μ) * freq_prob, ngram_prob being a character's conditional appearance probability given previous (n-1) characters and freq_prob being the overall appearance probability over the whole corpus.

    :param freq_dict: see output of get_freq().
    :param gram_dict: see output of get_ngram().
    :param accepted_chars: a set holding all accepted characters.
    :param smoothing_factor: the parameter μ used in computing loss.
    :param verbose: provide verbose output or not.
    :return: a dictionary holding the loss of one viterbi layer. Its structure is the very same as gram_dict.

    """
    if verbose:
        print("start computing loss")
    begin_mark = (len(list(gram_dict.keys())[0])) * begin_char
    default_mark = (len(list(gram_dict.keys())[0])) * default_char
    loss_dict = {}
    total_freq = sum(freq_dict.values())

    for c in accepted_chars:
        # if a character is not present in the corpus
        # we set its frequency to 1 to avoid math error
        freq_dict[c] = freq_dict.get(c, 1) / total_freq

    for query_str in gram_dict:
        loss_dict[query_str] = {}
        total = sum(gram_dict[query_str].values())
        for c in gram_dict[query_str]:
            loss_dict[query_str][c] = - log(
                smoothing_factor * gram_dict[query_str].get(c, 0) / total +
                (1 - smoothing_factor) * freq_dict[c]
            )
    loss_dict[begin_mark] = {}
    total = sum(gram_dict[begin_mark].values())
    for c in accepted_chars:
        loss_dict[begin_mark][c] = - log(
            smoothing_factor * gram_dict[begin_mark].get(c, 0) / total +
            (1 - smoothing_factor) * freq_dict[c]
        )

    # add default losses
    for key in freq_dict:
        freq_dict[key] = -log(freq_dict[key])
    loss_dict[default_mark] = freq_dict
    print("done computing!")

    # pack them into one dictionary
    return {"smoothing": smoothing_factor, "losses": loss_dict}


def viterbi_ngram(pinyin: list[str], loss_dict: dict, pinyin_dict: dict, gram_count: int):
    # Each entry in a layer is of form added_char: (min_loss, prefix_str).
    # Both store what you would expect them to.
    begin_mark = begin_char * (gram_count - 1)
    prev_layer = {begin_char: (0, begin_mark)}
    curr_layer = {}
    default_mark = default_char * (gram_count - 1)
    factor_loss = -log(1 - loss_dict['smoothing'])
    loss_dict = loss_dict['losses']

    for syl in pinyin:
        if syl not in pinyin_dict:
            # panic: output an underscore and restart the sentence
            prev_best = min(prev_layer.values(), key=lambda t: t[0])
            curr_layer = {begin_mark: (prev_best[0], prev_best[1] + '_')}
        else:
            for char in pinyin_dict[syl]:
                prev_best_key = ''
                min_loss = math.inf
                for key in prev_layer:
                    ngram_prefix = prev_layer[key][1][1 - gram_count:]
                    loss = prev_layer[key][0] + loss_dict.get(ngram_prefix, loss_dict[default_mark]).get(
                        char, factor_loss + loss_dict[default_mark][char])
                    if loss < min_loss:
                        min_loss = loss
                        prev_best_key = key
                curr_layer[char] = (min_loss, prev_layer[prev_best_key][1] + char)
        prev_layer = curr_layer
        curr_layer = {}

    return prev_layer[min(prev_layer, key=lambda k: prev_layer[k][0])][1][gram_count - 1:]


def demo():
    print(time.time())
    with open('weibo_loss.json', mode='r', encoding='utf-8') as fi:
        loss_dict = json.load(fi)
    print(time.time())
    with open('pinyin_to_hanzi.json', mode='r', encoding='utf-8') as fi:
        pinyin_dict = json.load(fi)
    print(time.time())

    while True:
        py = input()
        py = py.strip().split()
        print(viterbi_ngram(py, loss_dict, pinyin_dict, 2))


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


def demo_validate():
    with open('sina_loss.json', mode='r', encoding='utf-8') as fi:
        loss_dict = json.load(fi)
    with open('pinyin_to_hanzi.json', mode='r', encoding='utf-8') as fi:
        pinyin_dict = json.load(fi)
    print('file loaded')

    validate(lambda t: viterbi_ngram(t.split(), loss_dict, pinyin_dict, 3), Path('3gram_output.txt'))


def train(corpus_name: str, gram_count: int):
    with open('pinyin_to_hanzi.json', mode='r', encoding='utf-8') as fi:
        pinyin_dict = json.load(fi)
    print("Pinyin dictionary loaded")
    fi = open('corpus/%d.txt' % corpus_name, mode='r', encoding='utf-8')
    accepted_chars = set([char for group in pinyin_dict.values() for char in group])

    count = 0
    corpus = []
    gram_dict = MyDict()
    freq_dict = MyDict()
    print("Start training")
    t0 = time.time()
    for line in fi:
        corpus.append(line.strip().replace(begin_char, ''))
        count += 1
        if count % 100000 == 0:
            t1 = time.time()
            print("%d records trained in %d secs" % (count, int(t1 - t0)))
            corp = wash_corpus(corpus, accepted_chars)
            get_freq(corp, freq_dict, False)
            get_ngram(corp, gram_count, gram_dict, False)
            corpus.clear()
    corp = wash_corpus(corpus, accepted_chars)
    get_freq(corp, freq_dict, False)
    get_ngram(corp, gram_count, gram_dict, False)
    t1 = time.time()
    print("%d records trained in %d secs; frequency statistics completed" % (count, int(t1 - t0)))
    loss_dict = compute_loss(freq_dict, gram_dict, accepted_chars, 0.9999, True)
    t2 = time.time()
    print("Probabilistic data computed in %d secs" % int(t2 - t1))
    print("Finished training on corpora %s in %d seconds" % (corpus_name, int(t2 - t0)))
    with open('%s_%d_loss.json' % (corpus_name, gram_count), mode='w', encoding='utf-8') as fo:
        json.dump(loss_dict, fo)
    t3 = time.time()
    print("Written to disk in %d secs" % int(t3 - t2))


if __name__ == '__main__':
    pass
