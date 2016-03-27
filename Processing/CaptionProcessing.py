import re
import glob
import csv
from os.path import basename, join, splitext
from sqlalchemy import *

# CONSTANTS
# Database
ID_MVAD = 'MVAD'
ID_MPII = 'MPII'
# CSV COLUMNS
CSV_SRT_COL = 0
CSV_NAME_COL = 1
CSV_TIME_COL = 2
CSV_TEXT_COL = 3

class Caption:
    def __init__(self):
        self.text = ''
        self.video_name = ''
        self.video_path = ''
        self.action = ''
        self.movie = ''
        self.dataset = ''

def build_captions_from_actions(actions_path, dataset_id, actions_ext='txt'):
    engine = create_engine('mysql://annotator:multicomp@atlas4.multicomp.cs.cmu.edu/annodb')
    captions = []
    for action_filename in glob.glob(join(actions_path, '*.%s')%(actions_ext)):
        action = splitext(basename(action_filename))[0]
        action_file = open(join(actions_path, action_filename))
        caption_reader = csv.reader(action_file, delimiter='\t')
        for caption_input in caption_reader:
            #TODO: obtain the required data
            # Extract text
            text = caption_input[CSV_TEXT_COL]
            video_name = caption_input[CSV_NAME_COL]
            # Extract video path and movie
            info_query = 'SELECT video_path, movie FROM allvideos WHERE video_name="%s"'%(video_name)
            db_res = engine.execute(info_query)
            video_path = db_res[0][0]
            movie = db_res[0][1]
            
            new_caption = Caption()
            new_caption.action = action
            new_caption.text = text
            new_caption.video_name = video_name
            new_caption.video_path = video_path
            new_caption.movie = movie
            new_caption.dataset = dataset_id
            captions.append(new_caption)
            
    return captions

def store_in_db(captions):
    engine = create_engine('mysql://annotator:multicomp@atlas4.multicomp.cs.cmu.edu/annodb')
    
    for caption from captions:
        query = "INSERT INTO captions (text, video_name, video_path, action, movie, dataset) VALUES ('%s','%s','%s')"\
            %(caption.text, caption.video_name, caption.video_path, caption.action, caption.movie, caption.dataset)
        db_res = engine.execute(query)

def main():
    mvad_actions_path = ''
    mvad_captions = build_captions_from_actions(mvad_actions_path, ID_MVAD, 'csv')
    store_in_db(mvad_captions)
    
    mpii_actions_path = ''
    mpii_captions = build_captions_from_actions(mpii_actions_path, ID_MPII, 'csv')
    store_in_db(mpii_captions)
    
    
if __name__=='__main__':
    main()