import json
import time
import argparse
from pathlib import Path
from typing import Optional

from viterbi import viterbi_ngram


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

