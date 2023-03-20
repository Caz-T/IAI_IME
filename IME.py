import json
import time

begin_mark = '^^^'


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
    for sent in sents:
        if len(sent) == 0:
            continue
        if sent[0] in pinyin_dict:
            if begin_mark not in d:
                d[begin_mark] = {}
            first_syllable = pinyin_dict[sent[0]]
            if first_syllable not in d[begin_mark]:
                d[begin_mark][first_syllable] = {}
            d[begin_mark][first_syllable][sent[0]] = d[begin_mark][first_syllable].get(sent[0], 0) + 1

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
        return get_max_from_dict(ngram_dict[begin_mark][syllables[0]])
    answers = [get_max_from_dict(ngram_dict[begin_mark][syllables[0]]), ]
    for syl in syllables[1:]:
        try:
            answers.append(get_max_from_dict(ngram_dict[answers[-1]][syl]))
        except KeyError:
            answers.append(get_max_from_dict(ngram_dict[begin_mark][syl]))
    return "".join(answers)


def demo():
    with opr("2gram_sina", "json") as fi:
        ngram_dict = json.load(fi)
    print("loaded")
    while True:
        st = input()
        st = st.strip()
        print(parse_pinyin_by_ngram(st, ngram_dict))


def get_ngram():
    d = {}
    with opr('/Users/casorazitora/Desktop/Learn new stuff/大二下/人智导/输入法作业/语料库/sina_news') as fi:
        corpus = [line.strip() for line in fi.readlines()]
    with opr('/Users/casorazitora/Desktop/Learn new stuff/大二下/人智导/输入法作业/拼音汉字表/course_pinyin_dict', 'json') as fi:
        pinyin_dict = json.load(fi)
    print("loaded!")

    t0 = time.time()
    load_ngram_by_char(corpus, 2, d, pinyin_dict)
    t1 = time.time()
    print("load 2gram: %d secs" % int(t1 - t0))
    with opw('2gram_sina', 'json') as fo:
        json.dump(d, fo)
    t2 = time.time()
    print("write to disk: %d secs" % int(t2 - t1))


def get_char_freq():
    d = {}
    with opr('/Users/casorazitora/Desktop/Learn new stuff/大二下/人智导/输入法作业/语料库/sina_news') as fi:
        corpus = [line.strip() for line in fi.readlines()]
    with opr('/Users/casorazitora/Desktop/Learn new stuff/大二下/人智导/输入法作业/拼音汉字表/course_pinyin_dict', 'json') as fi:
        pinyin_dict = json.load(fi)

    t0 = time.time()
    load_char_freq(corpus, d, pinyin_dict)
    t1 = time.time()
    print("load freq: %d secs" % int(t1 - t0))
    with opw('word_freq_sina', 'json') as fo:
        json.dump(d, fo)
    t2 = time.time()
    print("write to disk: %d secs" % int(t2 - t1))


def validate(predict_function):
    with opr('validation/input') as fi:
        valid_set = [line.strip() for line in fi]
    with opr('validation/std_output') as fi:
        std_output = [line.strip() for line in fi]

    char_count = sum([len(t) for t in std_output])
    corr_char = 0
    corr_sent = 0
    for i in range(len(valid_set)):
        prediction = predict_function(valid_set[i])
        if len(prediction) != len(std_output):
            continue
        flag = True
        for j in range(len(prediction)):
            if prediction[j] == std_output[i][j]:
                corr_char += 1
            else:
                flag = False
        if flag:
            corr_sent += 1

    print("By character: %d / %d, accuracy %.4f" % (corr_char, char_count, corr_char / char_count))
    print("By sentence: %d / %d, accuracy %.4f" % (corr_sent, len(valid_set), corr_sent / len(valid_set)))


if __name__ == '__main__':
    get_char_freq()

