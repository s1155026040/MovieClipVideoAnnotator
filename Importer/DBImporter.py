
import os
import glob
import csv  
from sqlalchemy import *

def init_mysql_engine(host, username, password, db_name):
    return create_engine('mysql://%s:%s@%s/%s'%(username, password, host, db_name))

def insert_video(path, movie, length, caption, action, dataset)

def import_mvad_videos():
    db_engine = init_mysql_engine('atlas4.multicomp.cs.cmu.edu', 'annotator', 'multicomp', 'annodb')
    action_list_dir = './data'
    for action_file in glob.glob( os.path.join(action_list_dir, '*.csv') ):
        print action_file
        action_reader = csv.reader(open(action_file), delimiter='\t')
        for row in action_reader:
            print ' <> '.join(row)
        
if __name__=='__main__':
    import_mvad_videos()