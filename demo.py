import argparse
import json
from viterbi import viterbi_ngram

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Input method interactive demo.')
    arg_parser.add_argument('-l', '--loss-dict', type=str, default='loss.json',
                            help='path to loss dictionary trained with train.py')
    arg_parser.add_argument('-p', '--pinyin-dict', type=str, default='pinyin_dict.json',
                            help='path to pinyin dictionary. Leave blank for default')
    args = arg_parser.parse_args()

    try:
        fi = open(args.pinyin_dict, mode='r', encoding='utf-8')
        pinyin_dict = json.load(fi)
    except FileNotFoundError:
        print("Pinyin dictionary not found! "
              "Check whether pinyin_dict.json is placed in the same folder as this script.")
        exit(1)
    try:
        loss_file = open(args.loss_dict, mode='r', encoding='utf-8')
        loss_dict = json.load(loss_file)
    except FileNotFoundError:
        print("Loss dictionary not found!")
        exit(1)
    print("Loaded!")

    while True:
        pys = input("Type in pinyin string separated with space:")
        if len(pys.strip()) == 0:
            break
        pys = pys.split()
        print(viterbi_ngram(pys, loss_dict, pinyin_dict))
