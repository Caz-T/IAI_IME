import json


with open('no_tone.json', mode='r', encoding='utf-8') as fi:
    ori_d = json.load(fi)
with open('corpus/accepted_chars.txt', mode='r', encoding='utf-8') as fi:
    acc_c = "".join([l.strip() for l in fi.readlines()])

new_d = {}
for char in acc_c:
    if char not in ori_d:
        print(char, end=' ')
        continue
    if ori_d[char] not in new_d:
        new_d[ori_d[char]] = []
    new_d[ori_d[char]].append(char)

with open('outer.json', mode='w', encoding='utf-8') as fo:
    json.dump(new_d, fo)

