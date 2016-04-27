import os
import sys
import VideoToGif as v2g
import AnnotationDB as adb
import rawdataLoad as rdl
import multiprocessing as mp


# Constants
DATASETS_PATH = '/multicomp/datasets/'
GIF_PATH = '/home/zal/dataset_gifs'

# Connect to the DB
db = adb.AnnotationDB()
connected = db.init('atlas4.multicomp.cs.cmu.edu', 'annotator', 'multicomp', 'annodb')
if not connected:
    print 'Could not connect to DB, closing program'
    sys.exit(-1)

print db.get_all_users()

# Load the data
raw_data = rdl.main(0)

# Start exporting the GIF files
N = 10;
n = 0
for caption, video_path in raw_data.test:

    try:
        caption_id = db.get_caption_id(video_path)
        gif_fn = '%06d.gif'%(caption_id)
        v2g.video_to_gif(os.path.join(DATASETS_PATH,video_path), 
                         os.path.join(GIF_PATH, gif_fn), resize=[427,240])
    except AttributeError:
        print 'There is no caption ID for %s'%(video_path)
        
     
            
    n += 1
    if n >= N:
        break
    
print 'Fin'
