import json
fi = open('拼音汉字表.txt', mode='r', encoding='utf-8')
d = {}
for line in fi:
	parts = line.strip().split()
	if len(parts) == 0:
		continue
	d[parts[0]] = parts[1:]

fo = open('pinyin_dict.json', mode='w', encoding='utf-8')
json.dump(d, fo)
