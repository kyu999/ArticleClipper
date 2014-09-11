# -*- coding:utf-8 -*-
import lxml.html
import re
from furl import furl
from difflib import SequenceMatcher
import sys, traceback
from boilerpipe.extract import Extractor
import requests

class Extraction(object):
    """
    内部で使っているboilerpipeは余計なものを摘出することは少ないが、本来の本文よりも小さく摘出する傾向にあるので
    それを踏まえて精度を高めた本文抽出を行っている。また、本文だけではなくてdomも取得できるようになっている
    もちろんただbodyタグでくくったような形ではなくて本来のdomである。
    """
    
    def __init__(self, url, needless_tags = ["script", "style", "noscript"]):
        whole_html = requests.get(url).content
        self.url = url
        self.top_dom = lxml.html.fromstring(whole_html)
        self.needless_tags = needless_tags
        
    def is_img(self, node):
        """
        image要素かどうか判断
        """
        return node.tag == "img"
    
    def is_subtitle(self, node):
        """
        見出し要素かどうか判断
        """
        subtitle_tags = ["h1", "h2", "h3", "h4", "h5"]
        return node.tag in subtitle_tags
    
    def is_invalid_tag(self, node):
        """
        必要のないタグかどうか判断
        """
        return node.tag in self.needless_tags
     
    def split_by_newline(self, text):
        """
        改行ごとに区切る
        """
        if not text:
            return []
        return text.strip(u"\n").split(u"\n")
            
    def get_front_and_behind_text(self):
        """
        推定の本文の前半分と後ろ半分を取得
        """
        estimated_text = Extractor(extractor='ArticleExtractor', url=self.url).getText()

        if not self.estimated_text:
            return (None, None)
        
        half_len_text = len(self.estimated_text)/2
        return (self.estimated_text[0: half_len_text],
                self.estimated_text[half_len_text: -1])
        
    # minimum_lenに関してはサンプルを用意してそこから学習させるのもいいかもしれない。    
    def get_match_rate(self, sentence, text, minimun_len = 10):
        """
        ２つの文字列の一致具合を返す
        sentenceは推定本文の一部、textは検証対象文字列。textはnodeごとに異なる
        """
        text_len = len(text)
        if text_len < minimun_len:
            return 0
        lcs = SequenceMatcher(None, sentence, text).find_longest_match(0, len(sentence), 0, text_len)
        
        return lcs.size * (len(sentence) / float(text_len))
    
    def get_text(self, node):
        """
        nodeからテキストを取得
        """
        try:
            text = node.text_content()
        except Exception as e:
            if node is None:
                return None
            text = node.text
        return text
    
    def find_most_matched_node(self, sentence):
        """
        sentenceが最も含まれる割合が高いdomを取得
        """
        len_sentence = len(sentence)
        max_matched_rate = 0
        matched_node = None

        for node in self.top_dom.iter():
            
            text = self.get_text(node)
                            
            if not text:
                continue
                
            len_text = len(text)
            this_match_rate = self.get_match_rate(sentence, text)
            
            # len_textとlen_sentenceの関係について確かめる必要あり
            if this_match_rate > max_matched_rate:
                matched_node = node
                max_matched_rate = this_match_rate
                            
        return matched_node                        
    
    def get_front_and_behind_dom(self):
        """
        本文の前半分と後ろ半分の含まれる割合が最も高いdomを取得
        """
        front_sentence, behind_sentence = self.get_front_and_behind_text()
        
        front_dom = self.find_most_matched_node(front_sentence)
        behind_dom = self.find_most_matched_node(behind_sentence)
        
        return (front_dom, behind_dom)                

    def find_same_parent(self, front_dom, behind_dom):
        """
        front_domとbehind_domを内包する最小の親domを取得
        """
        front_parents, behind_parents = set([front_dom]), set([behind_dom])

        # front, behindそれぞれの親たちの中で一致するものを捜索
        while front_dom is not None or behind_dom is not None:
            # ２つのnodeの親nodeを取得
            if front_dom is not None:
                front_dom = front_dom.getparent()
                front_parents.add(front_dom)
            if behind_dom is not None:
                behind_dom =behind_dom.getparent()
                behind_parents.add(behind_dom)
                
            same_parent_doms = front_parents.intersection(behind_parents)
                        
            if len(same_parent_doms) > 0:
                same_parent_dom = same_parent_doms.pop()
                return same_parent_dom
                
        return None
    
    def clean_dom(self, estimated_dom):
        """
        推定されたdomの中からscriptや広告部分を除去
        """
        
        if estimated_dom is None:
            return None
        
        for child in estimated_dom.iterchildren():
            if self.is_invalid_tag(child):
                estimated_dom.remove(child)
            if child.getchildren() is not None:
                self.clean_dom(child)
                
        return estimated_dom
    
    def clean_text(self, dom):
        """
        textから不必要なスクリプト部分等を削除する
        """
        whole_text = self.get_text(dom)
        
        for node in dom.iter():
            text = self.get_text(node)
            
            if self.is_invalid_tag(node):
                whole_text.replace(text, "")
                
        return whole_text

    def extract_main_dom(self):
        """
        本文を内包する最小のdomを返す
        """
        front_dom, behind_dom = self.get_front_and_behind_dom()
        parent_dom = self.find_same_parent(front_dom, behind_dom)
        return self.clean_dom(parent_dom)
    
    def extract_main_content(self):
        """
        boilerpipeより精度の高い本文抽出
        """
        return self.clean_text(self.extract_main_dom())
    
    def is_only_tab_space_empty(self, paragraph):
        """
        改行、タブ、空行文字のみかどうかを判定
        """
        garbage_pattern = re.compile(u'^[\t\r\n]+$')
        return garbage_pattern.match(paragraph) is not None