#!/usr/bin/env python
# 
# This program is used to annotate video files from movie
# datasets such as M-VAD or MPII through a Video GUI and
#
# Carnegie Mellon University
# author: Salvador Medina
# last update: 2016-03-19
#

import cv2
import re
import os
import glob
import fileinput
import fnmatch
import pdb
import tty, sys, termios
import select
import pickle
import nltk
import ConfigParser
import VideoToGif as v2g
import tkFileDialog
import unicodedata
from Tkinter import Tk
from AnnotationDB import *
from os.path import basename, join, splitext
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import deque
from collections import namedtuple

#Constants
VA_COLOR_WHITE = (230, 230, 230)
VA_COLOR_LIGHT_GRAY = (128, 128, 128)
VA_COLOR_LIGHT_GREEN = (128, 255, 128)
VA_COLOR_DARK_GREEN = (64, 128, 64)
VA_COLOR_YELLOW = (21, 232, 232)
VA_COLOR_RED = (39,45,229)
VA_COLOR_DARK_RED = (23,18,128)

def build_video_path(base_path, video_name):
    movie_name = re.search(r'(.*)_DVS\d*', video_name).group(1)
    return os.path.join(base_path, movie_name,'video',video_name+'.avi')

def build_videoframe_path(video_path, frame_num):
    return '%s_%d%s'%(os.path.splitext(video_path)[0], frame_num, '.gif')

def build_gif_name(video_path):
    new_name = os.path.splitext(video_path)[0] + '.gif'
    return os.path.basename(new_name)

def print_manual():
    print '''
    The keyboard controls for the video annotation tool are:
    
    Space  - Play / Pause
    
    N      - Step backwards
    M      - Step forward
    .      - Annotate
    X      - Start point @ current frame
    C      - End point   @ current frame
    S      - Start point @ first frame
    F      - End point   @ last frame
    J      - Jump to next file
    H      - Show keyboard controls
    ESC, Q - Exit program
    
    '''

def is_verb_in_sentence(verb, sentence):
    sentence = unicodedata.normalize('NFKD', sentence).encode('ascii','ignore')
    text = word_tokenize(sentence)
    lemmatizer = nltk.stem.WordNetLemmatizer()
    lemma_words = [lemmatizer.lemmatize(word, 'v') for word in text]
    return (verb in lemma_words)

def get_total_frames(video_file_path):
    video_capture = cv2.VideoCapture(video_file_path)
    ret, cur_frame = video_capture.read()
    total_frames = 0
    while ret:
        total_frames += 1
        ret, cur_frame = video_capture.read()
    
    return total_frames

def draw_playbar(img, cur_frame_pos, start_frame, end_frame, total_frames):
    img_height, img_width, img_channels = img.shape

    # Playbar Constants
    playbar_height = 5
    played_color = VA_COLOR_WHITE
    in_played_color = VA_COLOR_RED
    in_not_played_color = VA_COLOR_DARK_RED
    not_played_color = VA_COLOR_LIGHT_GRAY
    
    
    if cur_frame_pos > 0:
        # Calculate positions
        cur_pos = int(float(cur_frame_pos)/float(total_frames) * img_width)
        start_pos = cur_pos
        end_pos = cur_pos
        if start_frame != -1:
            start_pos = int(float(start_frame)/float(total_frames) * img_width)
        if end_frame != -1:
            end_pos = int(float(end_frame)/float(total_frames) * img_width)
        
        
        if start_pos < end_pos:
            # IN and OUT positions have been set
            # there are 3 cases:
            
            if cur_pos < start_pos: # Case A: cur_pos < start_pos
                # 1. Draw PLAYED bar                
                cv2.rectangle(img, (0,img_height-playbar_height), (cur_pos, img_height), played_color, -1)
                # 2. Draw NOT PLAYED bar
                cv2.rectangle(img, (cur_pos,img_height-playbar_height), (start_pos, img_height), not_played_color, -1)
                cv2.rectangle(img, (start_pos,img_height-playbar_height), (end_pos, img_height), in_not_played_color, -1)
                cv2.rectangle(img, (end_pos,img_height-playbar_height), (img_width, img_height), not_played_color, -1)
            elif cur_pos < end_pos: # Case B:  start_pos < cur_pos < end_pos
                # 1. Draw PLAYED bar
                cv2.rectangle(img, (0,img_height-playbar_height), (start_pos, img_height), played_color, -1)
                cv2.rectangle(img, (start_pos,img_height-playbar_height), (cur_pos, img_height), in_played_color, -1)
                # 2. Draw NOT PLAYED bar
                cv2.rectangle(img, (cur_pos,img_height-playbar_height), (end_pos, img_height), in_not_played_color, -1)
                cv2.rectangle(img, (end_pos,img_height-playbar_height), (img_width, img_height), not_played_color, -1)
            else: # Case C:  end_pos < cur_pos
                # 1. Draw PLAYED bar
                cv2.rectangle(img, (0,img_height-playbar_height), (start_pos, img_height), played_color, -1)
                cv2.rectangle(img, (start_pos,img_height-playbar_height), (end_pos, img_height), in_played_color, -1)
                cv2.rectangle(img, (end_pos,img_height-playbar_height), (cur_pos, img_height), played_color, -1)
                # 2. Draw NOT PLAYED bar
                cv2.rectangle(img, (cur_pos,img_height-playbar_height), (img_width, img_height), not_played_color, -1)                
            
        else:
            # 1. Draw PLAYED bar
            cv2.rectangle(img, (0,img_height-playbar_height), (cur_pos, img_height), played_color, -1)
            # 2. Draw NOT PLAYED bar
            cv2.rectangle(img, (cur_pos+1,img_height-playbar_height), (img_width, img_height), not_played_color, -1)
    else:
        
        cv2.rectangle(img, (0,img_height-playbar_height), (img_width, img_height), not_played_color, -1)
    
    return img

def draw_timer(img, cur_frame_pos, total_frames):
    img_height, img_width, img_channels = img.shape
    timer_text = "%d/%d"%(cur_frame_pos, total_frames)
    timer_pos = (img_width - 100,20)
    timer_color = VA_COLOR_WHITE
    cv2.putText(img, timer_text, timer_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, timer_color)
    return img

def draw_caption(img, caption):
    img_height, img_width, img_channels = img.shape
    caption_color = VA_COLOR_YELLOW
    caption_pos = (10, img_height-30)
    cv2.putText(img, caption, caption_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, caption_color)
    return img

def draw_overlay(img, cur_frame, start_frame, end_frame, total_frames, caption =''):
    overlayed_frame = draw_playbar(img, cur_frame, start_frame, end_frame, total_frames)
    overlayed_frame = draw_timer(overlayed_frame, cur_frame, total_frames)
    if caption != '':
        overlayed_frame = draw_caption(img, caption)
    return overlayed_frame

def display_video_capture(video_file_path, capture_dir='', caption=''):
    #Persist until a video frame is captured
    captured_file_name = ''
    captured_frame = False
    skipped = False
    exit = False
    start_frame = -1
    end_frame = -1
    total_frames = get_total_frames(video_file_path)
    frame_pos = 0
    video_filename = os.path.basename(os.path.splitext(video_file_path)[0])
    while not captured_frame and not skipped and not exit:
        # start the video capture objec
        # Player variables
        video_paused = False
        inbuffer_index = 0
        last_frame = frame_pos-1
        frame_buffer = deque(maxlen=total_frames)
        # Initialize video capture object
        video_capture = cv2.VideoCapture(video_file_path)
        ret, cur_frame_img = video_capture.read()
        if ret:
            frame_pos = 1
            frame_buffer.append((frame_pos, cur_frame_img))
        #While videocapture keeps on throwing videos
        while ret:
            if not video_paused:
                if inbuffer_index < 0:   #we are reading from buffer
                    _, cur_frame_img = frame_buffer[inbuffer_index]
                    inbuffer_index += 1
                else:
                    ret, cur_frame_img = video_capture.read()
                    frame_pos += 1  #always show from frame 2
                    frame_buffer.append((frame_pos, cur_frame_img))
            if ret:
                # Show the frame with overlay
                overlayed_frame = draw_overlay(cur_frame_img.copy(), frame_pos+inbuffer_index, start_frame, end_frame, total_frames, caption)
                cv2.imshow(video_filename, overlayed_frame)
                

                # Monitor keyboard input
                key = cv2.waitKey(33) # 33[ms] to achieve ~30 FPS

                if key == 32:  # SPACE: Toggle PAUSE / PLAY
                    video_paused = not video_paused
                    
                elif key == ord('n') or key == ord('N'):  # STEP BACK
                    video_paused = True
                    if len(frame_buffer) > 0 and len(frame_buffer)+inbuffer_index > 1:
                        inbuffer_index -= 1
                        _,cur_frame_img = frame_buffer[inbuffer_index]
                        
                elif key == ord('m') or key == ord('M'):  # STEP FORWARD
                    video_paused = True
                    if inbuffer_index < -1: #we are navigating within the buffer
                        inbuffer_index += 1
                        _,cur_frame_img = frame_buffer[inbuffer_index]
                    else:
                        inbuffer_index = 0
                        ret, cur_frame_img = video_capture.read()
                        frame_pos += 1  #always show from frame 2
                        frame_buffer.append((frame_pos, cur_frame_img))
                        
                elif key == ord('.'): # Store frame
                    # Capture current frame
                    if capture_dir is not '': 
                        # Used by EXPORT MODE
                        captured_file_name = video_file_path[0:len(video_file_path)-4] + '_%05d' %(frame_pos+inbuffer_index) + '.png'
                        print "Saving frame %s"%(captured_file_name)
                        cv2.imwrite(os.path.join(capture_dir,captured_file_name),cur_frame_img)
                    # Otherwise simply ANNOTATE the video
                    captured_frame = True
                    break
                
                elif key == ord('x') or key == ord('X'):    # Set START point
                    start_frame = frame_pos+inbuffer_index
                    if end_frame < start_frame:
                        end_frame = start_frame
                    print 'IN: %d     OUT: %d'%(start_frame, end_frame)
                
                elif key == ord('s') or key == ord('S'):    # Set START point at begininng of video
                    start_frame = 1
                    if end_frame < start_frame:
                        end_frame = start_frame
                    print 'IN: %d     OUT: %d'%(start_frame, end_frame)

                elif key == ord('c') or key == ord('C'):    # Set STOP point
                    end_frame = frame_pos+inbuffer_index
                    if start_frame > end_frame:
                        start_frame = end_frame
                    print 'IN: %d     OUT: %d'%(start_frame, end_frame)
                
                elif key == ord('f') or key == ord('F'):    # Set STOP point at end of video
                    end_frame = last_frame
                    if start_frame > end_frame:
                        start_frame = end_frame
                    print 'IN: %d     OUT: %d'%(start_frame, end_frame)
                    
                elif key == ord('e') or key == ord('E'):    # Export to a GIF file
                    if start_frame < end_frame:                        
                        
                        export_gif_path = os.path.join(capture_dir, build_gif_name(video_file_path))
                        print 'Exporting to: %s'%(export_gif_path)
                        v2g.video_to_gif(video_file_path, export_gif_path, start_frame, end_frame)
                        

                elif key == ord('j') or key == ord('J'):    # JUMP to next file
                    captured_frame = True
                    break
                elif key == 27 or key == ord('q') or key == ord('Q'): # ESC: exit program 
                    cv2.destroyWindow(video_filename)
                    exit = True
                    break
                
        cv2.destroyWindow(video_filename)
    
    return exit, skipped, start_frame, end_frame, captured_file_name

def export_movie(output_path):
    '''
    All the videos in the paths are shown to the user
    The player allows through keyboard input to play/pause and capture the video
    '''
    # Print the manual
    print_manual()
    exit = False
    
    while not exit:
        root = Tk()
        root.withdraw()
        video_file_path = tkFileDialog.askopenfilename(parent = root,
                                                       title='Select Video File',
                                                       filetypes=[('AVI','.avi'), ('MPEG-4', '.mp4')],
                                                       defaultextension='.mp4')
        
        exit, skipped, start_frame, end_frame, ss = display_video_capture(video_file_path, capture_dir=os.getcwd())
    
    print 'Closing program'

def annotate_movie_times(base_path, video_list_path, cc_dict_path, annotations_path, actions_dict_path, user_name):
    '''
    All the vidoes in the movie_path_list are shown to the user
    The player allows through keyboard input to play/pause, capture the video and set start/end times
    '''
    # Print the manual
    print_manual()    
    
    #Get list of videos from file
    #Target action is obtained from the video list name
    target_action = splitext(basename(video_list_path))[0]
    video_list = open(video_list_path).readlines()
    video_list = map(lambda x:x.strip(), video_list) #clean all the \r, \n, spaces, etc
   
    #Load the captions dictionary
    cc_dict = pickle.load(open(cc_dict_path))
    actions_dict = pickle.load(open(actions_dict_path))

    #Annotated index
    annotated_index ={}
    if os.path.isfile('annotatedIdx.p'):
        annotated_index = pickle.load(open('annotatedIdx.p'))
    #Annotation definition
    #is a tuple with (video_name, in, out, caption)
    
    annotation_list = []
    for video_name in video_list:
        caption = ''
        video_path = build_video_path(base_path, video_name)
        if video_name in cc_dict and video_name not in annotated_index:
            caption = cc_dict[video_name]
            actions = actions_dict[video_name]
            print 'Annotating: %s'%(video_name)
            print 'Target Action: %s'%(target_action)
            filtered_sents = [sentence for sentence in sent_tokenize(caption) if is_verb_in_sentence(target_action, sentence)]
            displayed_caption = '\n'.join(filtered_sents)
            print 'Caption:\n%s'%(displayed_caption)
            
            exit, skipped, start_frame, end_frame, ss = display_video_capture(video_path, caption=displayed_caption)
            if exit:
                print 'Closing program'
                break
            elif skipped:
                annotated_index[video_name]='skipped'                
            else:
                annotated_index[video_name]='annotated'
                annotation_list.append((video_name+'.avi', start_frame, end_frame, caption))
                new_line = '\t'.join((video_name+'.avi', str(start_frame), str(end_frame), caption)) + '\n'
                open(annotations_path, 'a').write(new_line)
                
            pickle.dump(annotated_index,open('annotatedIdx.p','wb'))

def build_init_file(filename):
    config = ConfigParser.ConfigParser()
    config.add_section('Dataset')
    config.add_section('Database')
    config.add_section('Annotation')
    config.add_section('Capture')
    
    config.set('Dataset', 'base_path', '/Users/zal/CMU/Fall2015/HCMMML/FinalProject/Dataset/MontrealVideoAnnotationDataset/DVDtranscription')
    
    config.set('Database', 'db_ip', 'atlas4.multicomp.cs.cmu.edu')
    config.set('Database', 'db_username', 'annotator')
    config.set('Database', 'db_password', 'multicomp')
    config.set('Database', 'db_name', 'annodb')
    
    config.set('Annotation', 'annotation_path', '')
    config.set('Annotation', 'cc_dict_path', 'all_captions_dict.p')
    config.set('Annotation', 'action_dict_path', 'all_video_action_dict.p')
    config.set('Annotation', 'video_list_path', '')
    
    config.set('Capture', 'output_dir', './')
    
    config.write(open(filename, 'w'))
    
    return config

def load_init_file():
    init_filename = 'videoannotator.ini'
    config = ConfigParser.ConfigParser()
    
    if os.path.isfile(init_filename):    
        config.read(init_filename)
    else:
        config = build_init_file(init_filename)
    
    return config

def start_export_mode():
    cfg = load_init_file()
<<<<<<< HEAD
    export_movie(cfg)

def do_nothing():
    return 1
=======
    export_movie(cfg.get('Capture', 'output_dir'))
>>>>>>> 968d4d723dac0d530f9ec4bb2b344e9bd9009b42

def start_annotation_mode():    
    cfg = load_init_file()
    #TODO: select user from the DB
    anno_db = AnnotationDB()
    if anno_db.init(cfg.get('Database', 'db_ip'), 
                 cfg.get('Database', 'db_username'), 
                 cfg.get('Database', 'db_password'), 
                 cfg.get('Database', 'db_name')):
        users = anno_db.get_users()
    else:
        print 'ERROR: Could not connect to database'
        print 'User:     %s'%cfg.get('Database', 'db_username')
        print 'Password: %s'%cfg.get('Database', 'db_password')
        print 'Host:     %s'%cfg.get('Database', 'db_ip')
        print 'DB Name:  %s'%cfg.get('Database', 'db_name')
        users = ['Unconnected']
    
    sel_idx, sel_user = select_menu('Select user for annotating session:', [name for id,name in users])
    
    annotate_movie_times(cfg.get('Dataset', 'base_path'), 
                         cfg.get('Annotation', 'video_list_path'), 
                         cfg.get('Annotation', 'cc_dict_path'), 
                         cfg.get('Annotation', 'annotation_path'), 
                         cfg.get('Annotation', 'action_dict_path'),
                         sel_user)

def exit_program():
    print 'Quitting session.'
    sys.exit(0)


def select_menu(title, options):
    sel_idx = -1
    
    while sel_idx not in range(1,len(options)+1):
        print title
        for idx, option_txt in enumerate(options):
            print '%d. %s'%(idx+1, option_txt)
        try:
            sel_idx = int(input())
        except:
            sel_idx = -1
        print ''
        
    return sel_idx-1, options[sel_idx-1]

if __name__ == '__main__': 
    '''
    Main entry point of the program
    '''    
    options_txt = ['Export', 'Annotate', 'Quit']
    options_fun = [start_export_mode, start_annotation_mode, exit_program]
    sel_idx, sel_option = select_menu('Select application mode:', options_txt)
    
    options_fun[sel_idx]()
    
    print 'Exit program'
