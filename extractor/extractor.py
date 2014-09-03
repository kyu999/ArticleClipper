mport lxml.html
import re
from furl import furl
from difflib import SequenceMatcher
import sys, traceback
from boilerpipe.extract import Extractor
import requests

class Extractor(object):
    """
    摘出した本文からその本文や必要な画像を含んだdomを返すクラス
    """
    
    def __init__(self, url, needless_tags = ["script", "noscript", "noscript"]):
        """
        top_dom == page全体のdom
        """
        whole_html = requests.get(url).content
        extractor = Extractor(extractor='ArticleExtractor', url=url)
        
        self.rough_estimated_text = extractor.getText()
        self.top_dom = lxml.html.fromstring(whole_html)
        self.host = furl(url).host
        self.needless_tags = needless_tags

        self.only_tag_pattern = re.compile(u'^[\t]+$')
        # hostを省略したurl指定(e.g. /photo/archives/....)の場合にホストを追加してあげる
        self.omit_host_pattern = re.compile(u"^[/]")
        
    def is_img(self, node):
        tag = node.tag
        return tag == "img"
    
    def is_subtitle(self, node):
        tag = node.tag
        subtitle_tags = ["h1", "h2", "h3", "h4", "h5"]
        return tag in subtitle_tags
    
    def is_invalid_tag(self, node):
        """
        必要のないタグを除去
        """
        tag = node.tag
        return tag in needless_tags
     
    def split_by_newline(self, text):
        """
        改行ごとに区切る
        """
        if not text:
            return []
        return text.strip(u"\n").split(u"\n")
    
    # def get_upper_and_lower_body(self):
        
        
    def get_head_and_tail_text(self):
        """
        摘出した本文の最初と最後の行を取得
        """
        sentences = self.split_by_newline(self.body_text)

        if sentences is not None:
            return (sentences[0], sentences[-1])
        
        return (None, None)

    def matched_rate(self, this, that):
        """
        ２つの文字列の一致具合を返す
        """
        that_len = len(that)
        matcher = SequenceMatcher(None, this, that).find_longest_match(0, len(this), 0, that_len)
        if that_len == 0:
            return 0
        return matcher.size / float(that_len)
    
    def get_text(self, node):
        try:
            text = node.text_content()
        except Exception as e:
            if not node:
                return None
            text = node.text
        return text
    
    def get_head_and_tail_dom(self):
        """
        本文の最初と最後のdomを取得
        """
        head_sentence, tail_sentence = self.get_head_and_tail_text()
        len_head, len_tail = len(head_sentence), len(tail_sentence)
        # head, tailそれぞれとの一致具合の最高値
        max_matched_head, max_matched_tail = 0, 0
        head_node, tail_node = None, None

        for node in self.top_dom.iter():
            
            text = self.get_text(node)
                            
            if not text:
                continue
                
            len_text = len(text)
            head_match_rate = self.matched_rate(head_sentence, text)
            tail_match_rate = self.matched_rate(tail_sentence, text)

            if head_match_rate > max_matched_head and len_text >= len_head:
                head_node = node
                max_matched_head = head_match_rate
            
            if tail_match_rate > max_matched_tail and len_text >= len_tail:
                tail_node = node
                max_matched_tail = tail_match_rate
                
        return (head_node, tail_node)                

    def get_container_dom(self, head_dom, tail_dom):
        """
        head_domとtail_domからそれらを内包する最小のdomを取得
        """
        head_parents, tail_parents = set([head_dom]), set([tail_dom])
        same_parent_dom = None

        # head, tailそれぞれの親たちの中で一致するものを捜索
        while head_dom is not None or tail_dom is not None:
            # ２つのnodeの親nodeを取得
            if head_dom is not None:
                head_dom = head_dom.getparent()
                head_parents.add(head_dom)
            if tail_dom is not None:
                tail_dom =tail_dom.getparent()
                tail_parents.add(tail_dom)
            same_parent_dom = head_parents.intersection(tail_parents)
            
            if len(same_parent_dom):
                break
                
        if not same_parent_dom:
            return None
        
        same_parent_dom = same_parent_dom.pop()
        
        return same_parent_dom
    
    def remove_garbage(self, head_dom, tail_dom, estimated_dom):
        """
        推定されたdomの中からscriptや広告部分を除去
        """
        found_tail = False
        
        if not estimated_dom:
            return None
        
        for child in estimated_dom.iterchildren():
            if found_tail:
                estimated_dom.remove(child)
            if self.is_invalid_tag(child):
                estimated_dom.remove(child)
            if child == tail_dom:
                found_tail = True
            if child.getchildren() is not None:
                self.remove_garbage(head_dom, tail_dom, child)
                
        return estimated_dom

    def extract_main_dom(self):
        """
        本文を内包する最小のdomを返す
        """
        head_dom, tail_dom = self.get_head_and_tail_dom()
        estimated_dom = self.get_container_dom(head_dom, tail_dom)
        cleaned_dom = self.remove_garbage(head_dom, tail_dom, estimated_dom)
        return cleaned_dom
    
    def is_only_tab_space_empty(self, paragraph):
        removed = paragraph.replace("\r", "").replace("\n", "").replace("\t", "").replace(" ", "")
        return len(removed) == 0
    
    """
    def clean_dom(self, dom):
        for node in dom.iter():
            text = self.get_text()
            
            if self.is_invalid_tag(node):
                t.replace(text, "")
                
        return node
    
    """
        
    def generate_formatted_content(self):
        main_dom = self.extract_main_dom()
        text = self.get_text(main_dom)
        
        if not main_dom:
            return None
        
        # script部分がtext_contentにより混ざってしまったのでその除去。scriptは基本直下なのでtextでおk
        for node in main_dom.iter():
            try:
                text = node.text_content()
            except Exception as e:
                text = node.text
            
            if self.is_invalid_tag(node):
                all_text.replace(text, "")
                
        storage = []
        splitted = all_text.split("\n")
            
        for node in main_dom.iter():
            text = node.text
            if self.is_img(node):
                src = node.get("src")
                if self.omit_host_pattern.match(src):
                    src = self.host + src
                storage.append({'type': "image", 'src': src})
            if self.is_subtitle(node):
                storage.append({'type': "subtitle", 'text': text})

        # imgとParagraphの順番がこのままではぐちゃぐちゃになるからインデントを下げる必要あり。
        for paragraph in splitted:
            if not paragraph or self.is_only_tab_space_empty(paragraph):
                continue
            storage.append({'type': "paragraph", 'text': paragraph.strip("\t")})
                
            
        return storage
