# -*- coding:utf-8 -*-
import extraction

f = open("sample_urls.text","r")

for url in f:
    extractor = extraction.Extraction(url)
    print "-------------"
    print extractor.extract_main_content()
    
f.close()
