ArticleClipper
==============

article extractor from web pages in python

what you need to install to begin with => 
   1. boilerpipe-python (https://github.com/misja/python-boilerpipe)
   2. jpype (https://github.com/originell/jpype)
   3. charade (https://pypi.python.org/pypi/charade/1.0.3)


   This small program make use of boilerpipe-python, that is quite similar with this program and the significant difference is whether it takes just main text or the dom itself(could also say, fetch image too) since we need to fetch dom itself cuz image plays quite important role obviously. In addition, boilerpipe-python does not perform well to japanese pages(have no idea about the other languages); specifically, it tends to fetch only a piece of article. In short, this is just a kinda helper program to improve perfomance of text extraction and getting dom itself unlike useual library.
