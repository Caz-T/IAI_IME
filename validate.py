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


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Validate existing HMM model.')
    arg_parser.add_argument('LOSS_DICT', type=str,
                            help='path to loss dictionary trained with train.py')
    arg_parser.add_argument('-p', '--pinyin-dict', default='pinyin_dict.json',
                            help='path to pinyin dictionary. Leave blank for default')
    arg_parser.add_argument('-o', '--output-path', default='',
                            help='path to parsed output. Leave blank to suppress writing to file')
    args = arg_parser.parse_args()

    try:
        loss_file = open(args.LOSS_DICT, mode='r', encoding='utf-8')
        loss_dict = json.load(loss_file)
    except FileNotFoundError:
        print("Loss dictionary not found!")
        exit(1)
    try:
        fi = open(args.pinyin_dict, mode='r', encoding='utf-8')
        pinyin_dict = json.load(fi)
    except FileNotFoundError:
        print("Pinyin dictionary not found. "
              "Check whether pinyin_dict.json is placed in the same folder as this script.")
        exit(1)
    print('file loaded')

    if args.output_dict == '':
        validate(lambda t: viterbi_ngram(t.split(), loss_dict, pinyin_dict))
    else:
        validate(lambda t: viterbi_ngram(t.split(), loss_dict, pinyin_dict), Path(args.output_dict))
