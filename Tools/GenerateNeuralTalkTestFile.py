#! /usr/local/env python
#
# This program generates the captions required for our
# custom NeuralTalk system with now works with videos
#
# Carnegie Mellon University
# author: Salvador Medina
# date: 2016/04/28


import json
import os
import sys
import datetime
import glob
import AnnotationDB as adb
import rawdataLoad as rdl

'''
The file requires 5 main fields:
1. info
2. licenses
3. type
4. images
5. annotations

Only images and annotation need to be generated according to our data
- info is a dict filled out with our information
- licenses is a copy of the original file captions_val2014.json
- type is a copy
'''

# CONSTANTS
KEYFRAMES_PATH = '/multicomp/datasets/KeyFrames/'

# Load original file
cocoJson = json.load(open('captions_val2014.json'))

# 1. INFO
info_field = {}
info_field['contributor']  = 'CMU LTI AMMML group'
info_field['date_created'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
info_field['description']  = 'This is the test data set for final report'
info_field['url']          = 'www.cmu.edu'
info_field['version']      = '0.1'
info_field['year']         = '2016'

# 2. LICENSES
licenses_field = cocoJson['licenses']

# 3. TYPE
type_field = 'captions'

# 4. IMAGES and ANNOTATIONS
#  load database
db = adb.AnnotationDB()
db.init('atlas4.multicomp.cs.cmu.edu', 'annotator', 'multicomp','annodb')
#  load raw data
raw_data = rdl.main(0)

# Capture the information from each test instance
images_field = []
annotations_field = []

for caption, video_path in raw_data.test[]:
    # Get the caption id
    caption_id = int(db.get_caption_id(video_path))
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    frame_query_str = os.path.join(KEYFRAMES_PATH,'%s*'%(video_name))
    frame_fn_list = glob.glob(frame_query_str)
    frame_fn_list.sort()
    
    for frame_num in range(0,len(frame_fn_list)):
        image_id = (caption_id*100) + frame_num #convention id number
        
        image_input = {}
        image_input['date_captured'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        image_input['file_name']     = os.path.basename(video_path)
        image_input['height']        = 240
        image_input['width']         = 427
        image_input['id']            = image_id
        image_input['license']       = 3
        image_input['url']           = frame_fn_list[frame_num] #obtained from glob
        images_field.append(image_input)
    
        # Image caption
        anno_input = {}
        anno_input['caption']  = caption
        anno_input['id']       = caption_id
        anno_input['image_id'] = image_id
        annotations_field.append(anno_input)

# Build final output
data = {}
data['info'] = info_field
data['images'] = images_field
data['licenses'] = licenses_field
data['annotations'] = annotations_field
data['type'] = 'captions'

json.dump(data, open('captions_test2016.json','w'))