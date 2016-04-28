import os
import sys
import argparse
import VideoToGif as v2g
import AnnotationDB as adb
import rawdataLoad as rdl
import multiprocessing as mp


def generate_gif(video_data):
    caption, video_path = video_data
    try:
        caption_id = db.get_caption_id(video_path)
        gif_fn = '%06d.gif'%(caption_id)
        v2g.video_to_gif(os.path.join(DATASETS_PATH,video_path), 
                         os.path.join(GIF_PATH, gif_fn), resize=[427,240])
    except AttributeError:
        print 'There is no caption ID for %s'%(video_path)  
        
def mp_generate_gif(video_data_list):
    pool = mp.Pool(processes=18)
    print 'Launching multiprocessing pool'
    results = pool.map(generate_gif, video_data_list)
    pool.close()
    print 'Waiting for pool to finish'
    pool.join()
    return results 

def process_video(video_id):
    # Constants
    DATASETS_PATH = '/multicomp/datasets/'
    GIF_PATH = '/home/zal/dataset_gifs'
    
    # Connect to the DB
    db = adb.AnnotationDB()
    connected = db.init('atlas4.multicomp.cs.cmu.edu', 'annotator', 'multicomp', 'annodb')
    caption_id = db.get_caption_id(video_path)
    gif_fn = '%06d.gif'%(caption_id)
    v2g.video_to_gif(os.path.join(DATASETS_PATH,video_path), 
                     os.path.join(GIF_PATH, gif_fn), resize=[427,240])

def process_dataset(dataset_dir):
    # Constants
    DATASETS_PATH = '/multicomp/datasets/'
    GIF_PATH = '/home/zal/dataset_gifs'
    
    # Connect to the DB
    db = adb.AnnotationDB()
    
    connected = db.init('atlas4.multicomp.cs.cmu.edu', 'annotator', 'multicomp', 'annodb')
    if not connected:
        print 'Could not connect to DB, closing program'
        sys.exit(-1)
    
    # Load the data
    raw_data = rdl.main(0)
    
    mp_generate_gif(raw_data.test[0:20])
    
    '''
    # Start exporting the GIF files
    for caption, video_path in raw_data.test[0:10]:
    
        try:
            caption_id = db.get_caption_id(video_path)
            gif_fn = '%06d.gif'%(caption_id)
            v2g.video_to_gif(os.path.join(DATASETS_PATH,video_path), 
                             os.path.join(GIF_PATH, gif_fn), resize=[427,240])
        except AttributeError:
            print 'There is no caption ID for %s'%(video_path)
    '''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This program generates gif files of the given numbers')
    parser.add_argument('-id', nargs='?',  type=int)
    parser.add_argument('-a', nargs='?',  type=str)
    args = parser.parse_args()
    print args.id
    
    if args.a is None:
        process_dataset(args.a)
    else:
        process_video(args.id)