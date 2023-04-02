from math import log, inf

begin_char = '^'
default_char = '#'


def viterbi_ngram(pinyin: list[str], loss_dict: dict, pinyin_dict: dict):
    # Each entry in a layer is of form added_char: (min_loss, prefix_str).
    # Both store what you would expect them to.
    gram_count = loss_dict['gram_count']
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
                min_loss = inf
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
