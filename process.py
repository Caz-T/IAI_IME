from pathlib import Path

doc = []
for pth in Path('corpus/rmrb').glob('*'):
    fi = pth.open(mode='r', encoding='utf-8')
    doc += [l.replace(' ', '') for l in fi.readlines()]
    fi.close()

fo = open('corpus/rmrb.txt', mode='w', encoding='utf-8')
fo.write("".join(doc))
fo.close()

doc = []
for pth in Path('corpus/chinese_wiki/163').glob('*'):
    try:
        fi = pth.open(mode='r', encoding='utf-8')
        doc += fi.readlines()
        fi.close()
    except:
        print(pth)

for pth in Path('corpus/chinese_wiki/164').glob('*'):
    try:
        fi = pth.open(mode='r', encoding='utf-8')
        doc += fi.readlines()
        fi.close()
    except:
        print(pth)

fo = open('corpus/wiki.txt', mode='w', encoding='utf-8')
fo.write("".join(doc))
fo.close()
