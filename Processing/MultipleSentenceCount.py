#!/usr/bin/env python
# 
# This script processes all the captions within the database
# In search of captions that have more than one sentence
#

from __future__ import division
import multiprocessing as mp
from nltk.tokenize import sent_tokenize
from sqlalchemy import * 

def ensure_ascii(inStr):
    '''
    Ensures the input string has only ASCII characters, otherwise replace it with space
    '''
    return ''.join([i if ord(i) < 128 else ' ' for i in inStr])

def mp_process_iterable(func, iterable):
    numThreads = mp.cpu_count()-1
    pool = mp.Pool(numThreads)
    
    res = pool.map(func, iterable)
    
    pool.close()
    pool.join()
    
    return res

def count_sent(sentence):
    return len(sent_tokenize(sentence))

def mp_count_sent(sentences):
    return mp_process_iterable(count_sent, sentences)

def get_all_captions():
    # DB extraction
    engine = create_engine('mysql://annotator:multicomp@atlas4.multicomp.cs.cmu.edu/annodb')
    captions_query = 'SELECT caption from allvideos'
    res = engine.execute(captions_query)

    # Format data and reformat for processing
    captions = [ensure_ascii(row[0]) for row in res]
    
    return captions
    
def main():
    print ''
    all_captions = get_all_captions()
    sent_count = mp_count_sent(all_captions)
    
    num_captions = len(all_captions)
    num_onesent_captions = sum([1 if x==1 else 0 for x in sent_count])
    
    one_sent_ratio = num_onesent_captions / num_captions
    print 'One-sentence captions:   %f'%(one_sent_ratio)
    print 'Multisentence captions:  %f'%(1-one_sent_ratio)

if __name__=='__main__':
    main()