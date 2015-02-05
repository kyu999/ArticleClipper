ArticleClipper
==============

### What is this?
Article extractor from web pages in python. This small program makes use of boilerpipe-python, that is quite similar with this program and the significant difference is whether it takes just main text or the dom itself(could also say, fetch image too) since we need to fetch dom itself quite often. In addition, boilerpipe-python does not perform well to japanese pages(have no idea about the other languages); specifically, it tends to fetch only a piece of article. In short, this is just a kinda helper program to improve perfomance of text extraction and enable you to extract dom itself.

### What you need to install

1. boilerpipe-python (https://github.com/misja/python-boilerpipe)
2. jpype (https://github.com/originell/jpype)
3. charade (https://pypi.python.org/pypi/charade/1.0.3)
