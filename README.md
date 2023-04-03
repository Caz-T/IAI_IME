# README

## 依赖

python >= 3.8 (更低版本的python3理论上也能运行）

argparse >= 1.4.0

## 文件树

```
.
├── README.md
├── construct.py
├── demo.py
├── get_pinyin_dict.py
├── pinyin_dict.json
├── train.py
├── validate.py
├── validation
│   ├── input.txt
│   └── std_output.txt
└── viterbi.py

```
可运行的文件包括`get_pinyin_dict.py`, `demo.py`, `validate.py`和`train.py`。`construct.py`是加权训练综合语料库的脚本，需要在`./src/corpus/`中包括全部五个语料库文件时才能运行。

## 准备工作

- **所有文件请先转换为utf-8编码。**
- 确定`./src/`路径下有`pinyin_dict.json`文件。如果要自定义拼音文件，请按照本课程的文件格式提供**utf-8**编码的`拼音汉字表.txt`并置入`./src/`路径下，然后运行`python ./src/get_pinyin_dict.py`。*也可以使用对应的命令行参数指定其他路径下的拼音文件。*
- 若要训练模型，请将换行分隔的语料放入单个txt文件中，并置入`./src/corpus/`路径下，命名为`{语料库名称}.txt`。*也可以使用对应的命令行参数指定其他路径下的语料库。*
- 若要测试模型，请将测试输入放入单个文件中，一行一条，命名为`input.txt`；再将对应的标准输出放入单个文件中，一行一条，命名为`std_output.txt`。将二者一并置入`./src/validation/`路径下。
- 若要使用开箱即用的demo，请将某个由`train.py`训练得到的`.json`文件重命名为`loss.py`并置于`./src/`路径下。*也可以使用对应的命令行参数指定其他路径下的模型。*

## 用法

```
python train.py weibo -d loss.json
python validate.py loss.json
python demo.py
```

这段代码会在微博数据库上（如果已经放入`./src/corpus/`路径）训练二元模型，模型参数保存在`./src/loss.json`中，然后用标准输入输出进行验证，在命令行输出准确率计算结果，最后以上面这个模型启动交互式输入输出界面，直到用户输入空字符串为止。

这仅仅是一个用例。`train.py`是训练脚本，`validate.py`是验证脚本，`demo.py`是交互式demo脚本。可运行`python {文件}.py -h`查阅详细的命令行参数和帮助信息。

