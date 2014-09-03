# -*- coding:utf-8 -*-
import lxml.html
import re
from furl import furl
from difflib import SequenceMatcher
import sys, traceback
from boilerpipe.extract import Extractor
import requests

class BoilerTest(object):
    
    def __init__(self):
        pass
    
    def get_urls(self, filename = "test_urls.csv"):
        urls = []
        f = open(filename, "r")
        for line in f:
            urls.append(unicode(line, "utf-8"))
        f.close()
        return urls
    
    def fetch_info(self):
        urls = self.get_urls()
        texts = []
        whole_contents = []
        for url in urls:
            extractor = Extractor(extractor='ArticleExtractor', url=url)
            texts.append(extractor.getText())
            whole_contents.append(requests.get(url).content)

        return urls, whole_contents, texts
    