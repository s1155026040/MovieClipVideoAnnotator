import os
import VideoToGif as v2g
import AnnotationDB as adb
import rawdataLoad as rdl
import multiprocessing as mp


# Constants
DATASETS_PATH = '/multicomp/datasets/'
GIF_PATH = '/home/zal/dataset_gifs'

# Load the data
raw_data = rdl.main(0)

# Connect to the DB
db = adb.AnnotationDB()
db.init('atlas4.multicomp.cs.cmu.edu', 'annotator', '', 'annodb')

# Start exporting the GIF files
N = 10;
n = 0
for caption, video_path in raw_data.test:
    try:
        caption_id = db.get_caption_id(video_path)
        v2g.video_to_gif(os.path.join(DATASETS_PATH,video_path), 
                         os.path.join(GIF_PATH, gif_path), resize=[427,240])
    except:
        print 'Could not obtain caption id for %s'%(video_path)
        
    if n >= N:
        break
    
print 'Fin'