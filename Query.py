#!/usr/bin/env python
# coding: utf-8

# In[8]:


import sys
import time
import os
import xml.sax
from tqdm import tqdm_notebook as tqdm
import re
from collections import defaultdict
import math
import bisect


# In[9]:

threshold = 10000
file = open('./index/secondary.txt', 'r')
words = file.readlines()


# In[10]:


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


# In[11]:


def get_postinglist(word):
    ind = bisect.bisect_right(words, word) - 1
    if ind == -1:
        return ''
    file = open('./index/index' + str(ind) + '.txt', 'r')
    line = file.readline().strip('\n')
    wrd = line.split(":")[0]
    while line:
        if wrd == word:
            return line.split(":")[1]
        line = file.readline().strip('\n')
        wrd = line.split(":")[0]
    return ''


# In[12]:


def get_title(doc_no):
    off = doc_no // threshold
    file = open("./titles/title" + str(off) + '.txt')
    return file.readlines()[doc_no % threshold].strip('\n')


# In[13]:


def count(stri, ch):
    if ch not in stri:
        return 0
    part = stri.split(ch)[1]
    cnt = re.split(r'[^0-9]+', part)[0]
    return int(cnt)


# In[14]:


f = open("totaldocs.txt", "r")
total_docs = int(f.readlines()[0].strip('\n')) + 1
print("Total documents : " + str(total_docs))

def process_doc(doc, idcs):
    doc = 'd' + doc
    doc_no = count(doc, 'd')
    for i in range(6):
        if i in idcs:
            if ftype[i] not in doc:
                continue
            term_freq[doc_no][i+1] += 1
            tf = count(doc, ftype[i])
            idf = math.log2(total_docs / doc.count(ftype[i]))
            term_freq[doc_no][7] += tf * idf
    term_freq[doc_no][0] = max(term_freq[doc_no][1:7])


# In[16]:


ftype = ['t', 'b', 'c', 'i', 'r', 'e']
field_type = ["title:", "body:", "category:", "infobox:",  "ref:", "links:"]
print("---------------Press 'q' for quitting------------------")
while 1:
    query = input()
    if query == 'q':
        break
    st = time.time()
    query = query.lower()
    idcs = []
    flag = 0

    for ind, field in enumerate(field_type):
        if field in query:
            flag = 1
            idcs.append(ind)

    term_freq = defaultdict(lambda : [0] * 8)

    if flag == 0:
        idcs.append(0)
        idcs.append(1)

        toks = tokenize(query)
        # print(toks)
        for tok in toks:
            post_list = get_postinglist(tok)
            if post_list == '':
                continue
            docs = post_list.split("d")[1:]
            for doc in docs:
                process_doc(doc, idcs)

        results = sorted(term_freq.items(), key=lambda x: x[1], reverse = True)

        for result in results[:10]:
            print(get_title(result[0]))
    else:
        for ind, field in enumerate(field_type):
            if field in query:
                exp = re.escape(field) + "(.*)"
                x = re.findall(exp, str(query))[0].split(" ")
                done = 0
                lis = []
                for term in x:
                    for f in field_type:
                        if f in term:
                            done = 1
                            break
                    if done == 1:
                        break
                    lis += tokenize(term)
                for tok in lis:
                    post_list = get_postinglist(tok)
                    if post_list == '':
                        continue
                    docs = post_list.split('d')[1:]
                    for doc in docs:
                        process_doc(doc, [ind])
        results = sorted(term_freq.items(), key=lambda x: x[1], reverse = True)
        for result in results[:10]:
            print(get_title(result[0]))

    print("\nTime taken: " + str(time.time() - st))


# In[ ]:




