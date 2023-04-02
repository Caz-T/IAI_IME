import json

from train import wash_corpus, get_freq, get_ngram, MyDict, compute_loss

corpora = ['weibo', 'sina_news', 'rmrb', 'tieba', 'wiki']
weight = [3012, 6, 142, 24, 18]

# weight is inversely proportional to file size
gram_dict = MyDict()
freq_dict = MyDict()
pinyin_dict = json.load(open('pinyin_dict.json', mode='r', encoding='utf-8'))
accepted_chars = set([char for group in pinyin_dict.values() for char in group])

for i in range(5):
    print("Parsing %s" % corpora[i])
    fi = open('./corpus/%s.txt' % corpora[i], mode='r', encoding='utf-8')
    corpus = []
    count = 0
    for line in fi:
        corpus.append(line.strip().replace('^', ''))
        count += 1
        if count % 100000 == 0:
            corp = wash_corpus(corpus, accepted_chars, False)
            get_freq(corp, freq_dict, False)
            get_ngram(corp, 3, gram_dict, False)
            corpus.clear()
            print("%d records trained" % count)
    corp = wash_corpus(corpus, accepted_chars, False)
    get_freq(corp, freq_dict, False)
    get_ngram(corp, 3, gram_dict, False)

    for key in gram_dict:
        for char in gram_dict.keys():
            gram_dict[key][char] *= weight[i]

loss_dict = compute_loss(freq_dict, gram_dict, accepted_chars, 0.9999, True)
fo = open('weighted.json', mode='w', encoding='utf-8')
json.dump(loss_dict, fo)
fo.close()
