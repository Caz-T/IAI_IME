# README

## 依赖

python >= 3.8 (更低版本的python3理论上也能运行）

argparse >= 1.4.0

## 文件树

```
.
├── README.md
├── corpus
│   ├── accepted_chars.txt
│   ├── sina_news.txt
│   └── weibo.txt
├── demo.py
├── pinyin_dict.json
├── process.py
├── train.py
├── validate.py
├── validation
│   ├── input.txt
│   └── std_output.txt
└── viterbi.py
```
可运行的文件包括`process.py`, `validate.py`, `train.py`
