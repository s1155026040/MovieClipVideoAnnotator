# 
# This program imports into the database the captions that were
# classified according to their verb (action)
# 
# 

import re
import glob
import csv
import os
import pickle
import progressbar
from os.path import basename, splitext
from sqlalchemy import *

# CONSTANTS
# Database
ID_MVAD = 'MVAD'
ID_MPII = 'MPII'
# CSV COLUMNS
MVAD_CSV_SRT_COL = 0
MVAD_CSV_NAME_COL = 1
MVAD_CSV_TIME_COL = 2
MVAD_CSV_TEXT_COL = 3
MPII_CSV_NAME_COL = 0
MPII_CSV_TEXT_COL = 1

class Caption:
    def __init__(self):
        self.text = ''
        self.video_name = ''
        self.video_path = ''
        self.action = ''
        self.movie = ''
        self.dataset = ''

def ensure_ascii(inStr):
    '''
    Ensures the input string has only ASCII characters, otherwise replace it with space
    '''
    return ''.join([i if ord(i) < 128 else ' ' for i in inStr])

def sql_format(inStr):
    inStr = ensure_ascii(inStr)
    inStr = inStr.strip()
    inStr = inStr.replace('\r', ' ')
    inStr = inStr.replace('\n', ' ')
    inStr = inStr.replace('%', '%%')
    inStr = inStr.replace("'", "\\'")
    inStr = inStr.replace('"', '\\"')
    return inStr

def format_caption(caption):
    caption.text = sql_format(caption.text)
    caption.action = sql_format(caption.action)
    caption.video_name = sql_format(caption.video_name)
    caption.video_path = sql_format(caption.video_path)
    caption.movie = sql_format(caption.movie)

    return caption

def build_captions_MVAD(actions_path, actions_ext='txt'):
    engine = create_engine('mysql://annotator:multicomp@atlas4.multicomp.cs.cmu.edu/annodb')
    dataset_id = ID_MVAD
    captions = []
    action_list_str = os.path.join(actions_path, '*.%s'%(actions_ext))
    print 'File filter: %s'%(action_list_str)
    pb = progressbar.ProgressBar(len(glob.glob(action_list_str))+1)
    pb.start()
    action_count = 0
    for action_filename in glob.glob(action_list_str):
        action = splitext(basename(action_filename))[0]
        action_file = open( action_filename)
        caption_reader = csv.reader(action_file, delimiter='\t')
        for caption_input in caption_reader:
            #TODO: obtain the required data
            # Extract text
            text = caption_input[MVAD_CSV_TEXT_COL]
            video_name = caption_input[MVAD_CSV_NAME_COL]
            # Extract video path and movie
            info_query = 'SELECT video_path, movie FROM allvideos WHERE video_name="%s"'%(video_name)
            db_res = engine.execute(info_query)
            res_list = [r for r in db_res]
            video_path = res_list[0][0]
            movie = res_list[0][1]
            
            new_caption = Caption()
            new_caption.action = action
            new_caption.text = text
            new_caption.video_name = video_name
            new_caption.video_path = video_path
            new_caption.movie = movie
            new_caption.dataset = dataset_id
            captions.append(new_caption)
            
            action_count += 1
            pb.update(action_count)
            
    pb.finish()
            
    return captions

def build_captions_MPII(actions_path, actions_ext='txt'):
    engine = create_engine('mysql://annotator:multicomp@atlas4.multicomp.cs.cmu.edu/annodb')
    dataset_id = ID_MPII
    captions = []
    action_list_str = os.path.join(actions_path, '*.%s'%(actions_ext))

    pb = progressbar.ProgressBar(len(glob.glob(action_list_str))+1)
    pb.start()
    action_count = 0    

    for action_filename in glob.glob(action_list_str):
        action = splitext(basename(action_filename))[0]
        action_file = open(action_filename)
        caption_reader = csv.reader(action_file, delimiter='\t')
        for caption_input in caption_reader:
            #TODO: obtain the required data
            # Extract text
            text = caption_input[MPII_CSV_TEXT_COL]
            video_name = caption_input[MPII_CSV_NAME_COL]
            # Extract video path and movie
            info_query = 'SELECT video_path, movie FROM allvideos WHERE video_name="%s"'%(video_name)
            db_res = engine.execute(info_query)
            res_list = [r for r in db_res]
            video_path = res_list[0][0]
            movie = res_list[0][1]
            
            new_caption = Caption()
            new_caption.action = action
            new_caption.text = text
            new_caption.video_name = video_name
            new_caption.video_path = video_path
            new_caption.movie = movie
            new_caption.dataset = dataset_id
            captions.append(new_caption)
            action_count += 1
            pb.update(action_count)    
            
    pb.finish()
            
    return captions

def store_in_db(captions):
    if len(captions) < 1:
        print 'ERROR: CaptionProcesing::store_in_db - Captions has length zero'
        return
    
    engine = create_engine('mysql://annotator:multicomp@atlas4.multicomp.cs.cmu.edu/annodb')    

    caption_count = 0
    pb = progressbar.ProgressBar(len(captions)+1)
    pb.start()
    
    for caption in captions:
        caption = format_caption(caption)
        query = 'INSERT INTO captions (text, video_name, video_path, action, movie, dataset) VALUES ("%s","%s","%s","%s","%s","%s")'\
            %(caption.text, caption.video_name, caption.video_path, caption.action, caption.movie, caption.dataset)
        db_res = engine.execute(query)
        caption_count += 1
        pb.update(caption_count)
    
    pb.finish()

def main():
    # MVAD
    print 'Processing caption files for MVAD'
    mvad_actions_path = './Montreal_Verbs'
    print 'Storing captions in DB'
    mvad_captions = build_captions_MVAD(mvad_actions_path, 'txt')
    store_in_db(mvad_captions)
    print 'Finished uploading the MVAD captions'
    
    # MPII
    print 'Processing caption files for MPII'
    mpii_actions_path = './MPII_Verbs'    
    mpii_captions = build_captions_MPII(mpii_actions_path, 'txt')
    print 'Storing captions in DB'
    store_in_db(mpii_captions)
    print 'Finished uploading the MPII captions'
    
    print 'Program finished successfully'
    
    
if __name__=='__main__':
    main()