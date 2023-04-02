import json
import time
import argparse
from pathlib import Path
from math import log
from typing import Optional


class MyDict(dict):
    """
    Convenience custom class, supporting dict-like operations and value increment.
    """
    def incr(self, key, val=1):
        self[key] = self.get(key, 0) + val


begin_char = '^'
default_char = '#'


def wash_corpus(corpus: list[str], accepted_chars: set, verbose: bool = True):
    if verbose:
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

    count = 0
    t = time.time()
    for sent in corpus:
        count += 1
        if count % 10000 == 0:
            newt = time.time()
            if verbose:
                print("%d / %d sentences parsed in %d seconds" % (count, len(corpus), newt - t))
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
    if verbose:
        print("done computing!")

    # pack them into one dictionary
    return {"gram_count": len(list(gram_dict.keys())[0]) + 1, "smoothing": smoothing_factor, "losses": loss_dict}


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description="Course project 1 for IAI 2023 Spring. "
                                                     "Trains a n-gram hidden Markov model for Viterbi probing.")
    arg_parser.add_argument('CORPUS_NAME', type=str,
                            help='name of corpus (place the corpus file in ./corpus/ and name it {corpus_name}.txt')
    arg_parser.add_argument('-p', '--pinyin-dict', type=str, default='pinyin_dict.json',
                            help='path to pinyin-to-hanzi dictionary in json format')
    arg_parser.add_argument('-d', '--dest', type=str, default='',
                            help='path to desired destination of training result')
    arg_parser.add_argument('-s', '--smoothing', type=float, default=0.9999,
                            help='smoothing factor')
    arg_parser.add_argument('-g', '--gram-count', type=int, default=2,
                            help='gram count in training')
    arg_parser.add_argument('-v', '--verbose', action='store_true',
                            help='whether to provide verbose output')
    arg_parser.add_argument('-m', '--memory-saving', action='store_true',
                            help='save memory by removing low-frequency n-grams. '
                                 'May worsen performance on tiny corpora')

    args = arg_parser.parse_args()

    try:
        with open(args.pinyin_dict, mode='r', encoding='utf-8') as fi:
            pinyin_dict = json.load(fi)
    except FileNotFoundError:
        print("Pinyin dictionary not found. "
              "Check whether pinyin_dict.json is placed in the same folder as this script.")
        exit(1)
    if args.verbose:
        print("Pinyin dictionary loaded")
    fi = open('corpus/%s.txt' % args.CORPUS_NAME, mode='r', encoding='utf-8')
    accepted_chars = set([char for group in pinyin_dict.values() for char in group])

    count = 0
    corpus = []
    gram_dict = MyDict()
    freq_dict = MyDict()
    if args.verbose:
        print("Start training")
    t0 = time.time()
    for line in fi:
        corpus.append(line.strip().replace(begin_char, ''))
        count += 1
        if count % 100000 == 0:
            t1 = time.time()
            corp = wash_corpus(corpus, accepted_chars, False)
            get_freq(corp, freq_dict, False)
            get_ngram(corp, args.gram_count, gram_dict, False)
            corpus.clear()
            if args.memory_saving:
                for key in gram_dict:
                    new_d = MyDict()
                    for char in gram_dict[key]:
                        if gram_dict[key][char] > 1:
                            new_d[char] = gram_dict[key][char]
                    gram_dict[key] = new_d
            if args.verbose:
                print("%d records trained in %d secs" % (count, int(t1 - t0)))
    corp = wash_corpus(corpus, accepted_chars, False)
    get_freq(corp, freq_dict, False)
    get_ngram(corp, args.gram_count, gram_dict, False)
    t1 = time.time()
    if args.verbose:
        print("%d records trained in %d secs; frequency statistics completed" % (count, int(t1 - t0)))
    loss_dict = compute_loss(freq_dict, gram_dict, accepted_chars, args.smoothing, args.verbose)
    t2 = time.time()
    if args.verbose:
        print("Probabilistic data computed in %d secs" % int(t2 - t1))
        print("Finished training on corpora %s in %d seconds" % (args.CORPUS_NAME, int(t2 - t0)))
    if args.dest != '':
        fo = open(args.dest, mode='w', encoding='utf-8')
    else:
        fo = open('%s_%d_loss%s.json' % (args.CORPUS_NAME, args.gram_count, "_small" if args.memory_saving else ''),
                  mode='w', encoding='utf-8')
    json.dump(loss_dict, fo)
    fo.close()
    t3 = time.time()
    if args.verbose:
        print("Written to disk in %d secs" % int(t3 - t2))


