# -*- coding:utf-8 -*-
import lxml.html
import re
from furl import furl
from difflib import SequenceMatcher
import sys, traceback
from boilerpipe.extract import Extractor
import requests

class Extraction(object):
    
    def __init__(self, url, needless_tags = ["script", "noscript", "noscript"]):
        whole_html = requests.get(url).content
        extractor = Extractor(extractor='ArticleExtractor', url=url)
        
        self.estimated_text = extractor.getText()
        self.top_dom = lxml.html.fromstring(whole_html)
        self.host = furl(url).host
        self.needless_tags = needless_tags
        
    def is_img(self, node):
        tag = node.tag
        return tag == "img"
    
    def is_subtitle(self, node):
        tag = node.tag
        subtitle_tags = ["h1", "h2", "h3", "h4", "h5"]
        return tag in subtitle_tags
    
    def is_invalid_tag(self, node):
        """
        必要のないタグかどうか判断
        """
        tag = node.tag
        return tag in self.needless_tags
     
    def split_by_newline(self, text):
        """
        改行ごとに区切る
        """
        if not text:
            return []
        return text.strip(u"\n").split(u"\n")
            
    def get_front_and_behind_text(self):
        """
        摘出した本文の前半分と後ろ半分を取得
        """
        if not self.estimated_text:
            return (None, None)
        
        half_len_text = len(self.estimated_text)/2
        return (self.estimated_text[0: half_len_text],
                self.estimated_text[half_len_text: -1])
        
    def get_match_rate(self, this, that):
        """
        ２つの文字列の一致具合を返す
        """
        that_len = len(that)
        matcher = SequenceMatcher(None, this, that).find_longest_match(0, len(this), 0, that_len)
        if that_len <= 0:
            return 0
        return matcher.size / float(that_len)
    
    def get_text(self, node):
        """
        nodeからテキストを取得
        """
        try:
            text = node.text_content()
        except Exception as e:
            if not node:
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

            if this_match_rate > max_matched_rate and len_text >= len_sentence:
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

    def get_container_dom(self, head_dom, tail_dom):
        """
        front_domとbehind_domを内包する最小の親domを取得
        """
        head_parents, tail_parents = set([head_dom]), set([tail_dom])
        same_parent_doms = None

        # head, tailそれぞれの親たちの中で一致するものを捜索
        while head_dom is not None or tail_dom is not None:
            # ２つのnodeの親nodeを取得
            if head_dom is not None:
                head_dom = head_dom.getparent()
                head_parents.add(head_dom)
            if tail_dom is not None:
                tail_dom =tail_dom.getparent()
                tail_parents.add(tail_dom)
                
            same_parent_doms = head_parents.intersection(tail_parents)
            
            if same_parent_doms is not None:
                same_parent_dom = same_parent_doms.pop()
                return same_parent_dom
                
        return None
    
    # ここが本当に必要なのか確認する必要あり
    def clean_dom(self, head_dom, tail_dom, estimated_dom):
        """
        推定されたdomの中からscriptや広告部分を除去
        """
        
        if not estimated_dom:
            return None
        
        for child in estimated_dom.iterchildren():
            if self.is_invalid_tag(child):
                estimated_dom.remove(child)
            if child.getchildren() is not None:
                self.clean_dom(head_dom, tail_dom, child)
                
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
        main_dom = self.get_container_dom(front_dom, behind_dom)
        return self.clean_dom(front_dom, behind_dom, main_dom)
    
    def is_only_tab_space_empty(self, paragraph):
        """
        改行、タブ、空行文字のみかどうかを判定
        """
        gabarge_pattern = re.compile(u'^[\t\r\n]+$')
        return gabarge_pattern.match(paragraph) is not None
        
    def generate_formatted_content(self):
        """
        domではなく整形した形で本文を返す
        """
        main_dom = self.extract_main_dom()
        whole_text = self.clean_text(main_dom)
        
        if not main_dom:
            return None
                
        # hostを省略したurl指定(e.g. /photo/archives/....)の場合にホストを追加してあげる
        self.omit_host_pattern = re.compile(u"^[/]")
        
        article = []
            
        for node in main_dom.iter():
            text = node.text
            if self.is_img(node):
                src = node.get("src")
                if self.omit_host_pattern.match(src):
                    src = self.host + src
                article.append({'type': "image", 'src': src})
                continue
                
            if self.is_subtitle(node):
                article.append({'type': "subtitle", 'text': text})
                continue

            if not text:
                continue
                
            paragraphs = text.split("\n")
            
            for paragraph in paragraphs:
                if not paragraph or self.is_only_tab_space_empty(paragraph):
                    continue
                article.append({'type': "paragraph", 'text': paragraph.strip("\t")})
            
        return article
