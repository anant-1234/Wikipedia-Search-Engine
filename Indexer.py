#!/usr/bin/env python
# coding: utf-8

# In[82]:


# Imports

import sys
import time
import os
import xml.sax
from tqdm import tqdm_notebook as tqdm
import re
from collections import defaultdict
import math
import bisect

final_time = time.time()
threshold = 10000
# In[235]:
os.mkdir("index")
os.mkdir("titles")

class PageHandler( xml.sax.ContentHandler ) :
    total_pages = 0
    total_docs = 0
    def __init__(self):
        self.titles = []
        self.word_dict = {}
        self.file_cnt = 1
        self.page_no = 0
        self.data = ''
    def startElement(self, tag, attributes):
        self.data = ''
    def endElement(self, tag):
        if tag == "page":
            if self.page_no == self.file_cnt * threshold:
                write_to_disk(self.file_cnt, self.word_dict, self.titles)
                self.word_dict = {}
                self.titles = []
                self.file_cnt += 1
                PageHandler.total_pages += 1
            make_index(self.title, self.text, self.page_no, self.word_dict)
            (self.titles).append(self.title)
            PageHandler.total_docs = self.page_no
            self.page_no += 1
        elif tag == 'title':
            self.title = self.data
            self.data = ''
        elif tag == 'text':
            self.text = self.data
            self.data = ''
        elif tag == 'mediawiki':
            write_to_disk(self.file_cnt, self.word_dict, self.titles)
            self.word_dict = {}
            self.titles = []
            PageHandler.total_pages += 1
            print("Done")
    def characters(self, content):
        self.data += content       


# In[236]:



# Tokenization and Stemming

from spacy.lang.en.stop_words import STOP_WORDS
from Stemmer import Stemmer

stemmer = Stemmer('porter')

def tokenize(text):
    tokens = re.split(r'[^A-Za-z0-9]+', text)
    curated = []
    for token in tokens:
        word = stemmer.stemWord(token.lower())
        if len(word) <= 1 or word in STOP_WORDS:
            continue
        curated.append(word)
    return curated


# In[9]:


def get_category(text):
    lists = re.findall(r"\[\[Category:(.*)\]\]", str(text))
    ans = []
    for curr in lists:
        temp = tokenize(curr)
        ans += temp
    return ans


# In[8]:


def get_infobox(text):
    raw = text.split("{{Infobox")
    ans = []
    if len(raw) <= 1:
        return []
    for ind in range(1,len(raw)):
        traw = raw[ind].split("\n")
        for lines in traw:
            if lines == "}}":
                break
            ans += tokenize(lines)
    return ans


# In[7]:


def get_externallinks(text):
    raw = text.split("==External links==")
    ans = []
    if len(raw) <= 1:
        return []
    raw = raw[1].split("\n")
    for lines in raw:
        if lines and lines[0] == '*':
            line = tokenize(lines)
            ans += line
    return ans 


# In[6]:


def get_references(text):
    raw = text.split("==References==")
    ans = []
    if len(raw) <= 1:
        return []
    raw = raw[1].split("\n")
    for lines in raw:
        if ("[[Category" in lines) or ("==" in lines) or ("DEFAULTSORT" in lines):
            break
        line = tokenize(lines)
        if "Reflist" in line:
            line.remove("Reflist")
        if "reflist" in line:
            line.remove("reflist")
        ans += line
    return ans


# In[5]:


def make_index(title, text, page_no, word_dict):
    # Title words (Index : 0)
    title_tok = tokenize(title)
    process_field(page_no, 0, title_tok, word_dict)

    # Body (Index : 1)
    try:
        process_field(page_no, 1, tokenize(text), word_dict)
    except:
        pass

    # Category (Index : 2)
    process_field(page_no, 2, get_category(text), word_dict)

    # Infobox (Index : 3)
    process_field(page_no, 3, get_infobox(text), word_dict)

    # References (Index : 4)
    process_field(page_no, 4, get_references(text), word_dict)

    # External Links (Index : 5)
    process_field(page_no, 5, get_externallinks(text), word_dict)


# In[4]:


def process_field(page_no, index, tok_list, word_dict):
    for tok in tok_list:
        lis = [0, 0, 0, 0, 0, 0]
        if tok not in word_dict:
            lis[index] += 1
            word_dict[tok] = {}
            word_dict[tok][page_no] = lis
        else:
            old = word_dict[tok]
            if page_no not in old:
                lis[index] += 1
                word_dict[tok][page_no] = lis
            else:
                old = old[page_no]
                old[index] += 1
                word_dict[tok][page_no] = old


# In[233]:


# Writing to file index.txt

# ['title', 'body', 'category', 'infobox', 'references', 'external-links']

def write_to_disk(cntr, word_dict, titles):
    cntr = cntr - 1
    ftype = ['t', 'b', 'c', 'i', 'r', 'e']
    file = open('./index/index' + str(cntr) + '.txt', 'w')
    for ind, word in enumerate(sorted(word_dict.keys())):
        mystr = word + ':'
        for doc in word_dict[word]:
            freq = word_dict[word][doc]
            mystr += "d" + str(doc)
            for ind, fs in enumerate(freq):
                if fs > 0:
                    mystr += str(ftype[ind]) + str(fs)
        file.write(mystr + "\n")
    file.close()
    # print(cntr)
    file = open("./titles/title" + str(cntr) + ".txt", 'w')
    for title in titles:
        file.write(title + '\n')
    file.close()



f1 = sys.argv[1]
parser = xml.sax.make_parser()
parser.setFeature(xml.sax.handler.feature_namespaces, 0)

Handler = PageHandler()
parser.setContentHandler( Handler )
parser.parse(f1)
f = open('totaldocs.txt', 'w')
f.write(str(PageHandler.total_docs) + '\n')

# In[239]:


def getname(pt):
    return './index/index' + str(pt) + '.txt'


# In[240]:


def merge_2_files(pt1, pt2):
    if pt1 == pt2:
        return
    f1 = open(getname(pt1), 'r')
    f2 = open(getname(pt2), 'r')
    f3 = open('temp.txt', 'w')
    l1 = f1.readline().strip('\n')
    l2 = f2.readline().strip('\n')
    while (l1 and l2):
        word1 = l1.split(":")[0]
        word2 = l2.split(":")[0]
        if word1 < word2:
            f3.write(l1 + '\n')
            l1 = f1.readline().strip('\n')
        elif word2 < word1:
            f3.write(l2 + '\n')
            l2 = f2.readline().strip('\n')
        else:
            list1 = l1.strip().split(":")[1]
            list2 = l2.strip().split(':')[1]
            f3.write(word1 + ':' + list1 + list2 + '\n')
            l1 = f1.readline().strip('\n')
            l2 = f2.readline().strip('\n')
    while l1:
        f3.write(l1 + '\n')
        l1 = f1.readline().strip('\n')
    while l2:
        f3.write(l2 + '\n')
        l2 = f2.readline().strip('\n')
    os.remove(getname(pt1))
    os.remove(getname(pt2))
    os.rename('temp.txt', getname(pt1 // 2))


# In[242]:


st = time.time()
r = PageHandler.total_pages
print("Total files : " + str(r))

while r != 1:
    for i in range(0, r, 2):
        if i + 1 == r:
            new_name = i // 2
            os.rename(getname(i), getname(i // 2))
            break
        merge_2_files(i, i+1)
    if r % 2 == 1:
        r = r // 2 + 1
    else:
        r = r // 2
    print("Number of files left: " + str(r))

print("Time for merging : " + str(time.time() - st))


# In[243]:


total_files = 0
def split_sorted():
    file_cntr = 0
    os.rename(getname(0), './index/full.txt')
    file = open('./index/full.txt', 'r')
    sec = open('./index/secondary.txt', 'w')
    line = file.readline().strip('\n')
    lines = []
    while line:
        lines.append(line)
        if len(lines) % threshold == 0:
            writ = open(getname(file_cntr), 'w')
            sec.write(lines[0].split(":")[0] + '\n')
            for l in lines:
                writ.write(l + '\n')
            file_cntr += 1
            lines = []
        line = file.readline().strip('\n')
    if len(lines) > 0:
        writ = open(getname(file_cntr), 'w')
        sec.write(lines[0].split(":")[0] + '\n')
        for l in lines:
            writ.write(l + '\n')
        file_cntr += 1
        lines = []
    os.remove('./index/full.txt')
    file.close()
    sec.close()
    return file_cntr

total_files = split_sorted()


# In[244]:


print("Total files after splitting : " + str(total_files))

print("Total time : " + str(time.time() - final_time))
# In[ ]:




