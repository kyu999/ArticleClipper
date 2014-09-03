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
        """
        boilerpipeの本文抽出は余計な部分まで取得することは少ないけれど、本来より少ないことは多々ある
        """
        urls = self.get_urls()
        got_infos = []
        for url in urls:
            extractor = Extractor(extractor='ArticleExtractor', url=url)
            text = extractor.getText()
            content = requests.get(url).content
            got_infos.append([url, text, content])

        return got_infos
    
    def show_got_info(self):
        data = self.fetch_info()
        for each in data:
            print "-----------------"
            print each[0]
            print each[1]
    