
from os.path import basename, splitext
from sqlalchemy import *



def update_names():
    engine = create_engine('mysql://annotator:multicomp@atlas4.multicomp.cs.cmu.edu/annodb')
    db_res = engine.execute('SELECT video_path FROM allvideos')
    video_path_list = [x[0] for x in db_res]
    
    for video_path in video_path_list:
        video_name = splitext(basename(video_path))[0]
        update_query = "UPDATE allvideos SET video_name='%s' WHERE video_path='%s'"%(video_name, video_path)
        engine.execute(update_query)

if __name__=='__main__':
    update_names()