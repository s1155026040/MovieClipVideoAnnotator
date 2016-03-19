#!/usr/bin/env python
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
import pick
import ConfigParser
from os.path import basename, join, splitext
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import deque
from collections import namedtuple
from matplotlib import pyplot as plt

class VASettings:
    '''
    This is the datastructure that stores the capturing session
    '''
    base_path = ''
    output_path = ''
    video_dir = ''
    movie_dir = ''
    cc_dict_path = ''
    video_list_path = ''
    action_dict_path = ''
    
    def __init__(self, base_path='', output_path='', movie_dir='', video_dir='', cc_dict_path='', video_list_path='', action_dict_path=''):
        self.base_path = base_path
        self.output_path = output_path
        self.video_dir = video_dir
        self.movie_dir = movie_dir
        self.cc_dict_path = cc_dict_path
        self.video_list_path = video_list_path
        self.action_dict_path = action_dict_path

def build_video_path(base_path, video_name):
    movie_name = re.search(r'(.*)_DVS\d*', video_name).group(1)
    return os.path.join(base_path, movie_name,'video',video_name+'.avi')

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

VA_COLOR_WHITE = (230, 230, 230)
VA_COLOR_LIGHT_GRAY = (128, 128, 128)
VA_COLOR_LIGHT_GREEN = (128, 255, 128)
VA_COLOR_DARK_GREEN = (64, 128, 64)
VA_COLOR_YELLOW = (21, 232, 232)
VA_COLOR_RED = (39,45,229)
VA_COLOR_DARK_RED = (23,18,128)

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
        frame_buffer = deque(maxlen=60)
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
                        captured_file_name = video_file_path[0:len(video_file_path)-4] + '_%05d' %(frame_pos+inbuffer_index) + '.png'
                        print "Saving frame %s"%(captured_file_name)
                        cv2.imwrite(os.path.join(capture_dir,captured_file_name),cur_frame_img)
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

                elif key == ord('j') or key == ord('J'):    # JUMP to next file
                    captured_frame = True
                    break
                elif key == 27 or key == ord('q') or key == ord('Q'): # ESC: exit program 
                    cv2.destroyWindow(video_filename)
                    exit = True
                    break
                
        cv2.destroyWindow(video_filename)
    
    return exit, skipped, start_frame, end_frame, captured_file_name

def capture_movie_frames(base_path, path1, path2, out_path, cc_dict_path):
    '''
    All the videos in the paths are shown to the user
    The player allows through keyboard input to play/pause and capture the video
    '''
    # Print the manual
    print_manual()
    
    #Load the captions dictionary
    cc_dict = None
    if os.path.isfile(cc_dict_path):
        cc_dict = pickle.load(open(cc_dict_path, 'rb'))
    
    # make the output path if it does not exist
    if not os.path.isdir(os.path.join(out_path,path1)):
        os.makedirs(os.path.join(out_path,path1))
    
    #Go through all the video files in the folder
    for video_filename in os.listdir(os.path.join(base_path,path1,path2)):
        #We are only interested in the AVI video files
        if fnmatch.fnmatch(video_filename,'*.avi'):
            #If already screen capped, go to next file
            video_basename = os.path.splitext(os.path.basename(video_filename))[0]
            if len(glob.glob(os.path.join(out_path,path1)+'/'+video_basename+'*.png')) > 0:
                continue
            
            print video_filename
            if cc_dict is not None:
                video_filename_no_ext = os.path.splitext(video_filename)[0]
                if video_filename_no_ext in cc_dict:
                    print 'Seeking frame for'
                    print cc_dict[video_filename_no_ext]
                    video_file_path = os.path.join(base_path,path1,path2,video_filename)
                    display_video_capture(video_file_path, out_path)

def annotate_movie_times(base_path, video_list_path, cc_dict_path, annotations_path, actions_dict_path):
    '''
    All the vidoes in the movie_path_list are shown to the user
    The player allows through keyboard input to play/pause, capture the video and set start/end times
    '''
    # Print the manual
    print_manual()    
    
    #Get list of videos from file
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
            if not skipped:
                annotated_index[video_name]='annotated'
                annotation_list.append((video_name+'.avi', start_frame, end_frame, caption))
                new_line = '\t'.join((video_name+'.avi', str(start_frame), str(end_frame), caption)) + '\n'
                open(annotations_path, 'a').write(new_line)
            else:
                annotated_index[video_name]='skipped'
            pickle.dump(annotated_index,open('annotatedIdx.p','wb'))

def generate_init_file(filename):
    config = ConfigParser.ConfigParser()
    config.add_section('Dataset')
    config.add_section('Database')
    
    config.set('Dataset', 'base_path', '/Users/zal/CMU/Fall2015/HCMMML/FinalProject/Dataset/MontrealVideoAnnotationDataset/DVDtranscription')
    config.set('Dataset', 'output_path', '/Users/zal/CMU/Fall2015/HCMMML/FinalProject/Dataset/MontrealVideoAnnotationDataset/DVDTranscriptionKeyFrames')
    config.set('Dataset', 'movie_dir', 'THE_VOW')
    config.set('Dataset', 'video_dir', 'video')
    config.set('Dataset', 'cc_dict_path', '/Users/zal/CMU/Fall2015/HCMMML/FinalProject/Repository/DataProcessing/all_captions_dict.p')
    
    config.set('Database', 'db_ip', '')
    config.set('Database', 'db_username', '')
    config.set('Database', 'db_password', '')
    config.set('Database', 'db_name', '')
    
    config.write(open(filename, 'w'))
    
    return config

def load_init_settings():
    init_filename = 'videoannotator.ini'
    config = ConfigParser.ConfigParser()
    
    if os.path.isfile(init_filename):    
        config.read(init_filename)
    else:
        config = generate_init_file(init_filename)
    
    settings = VASettings( base_path=config['Dataset']['base_path'],
                        output_path=config['Dataset']['output_path'], 
                        movie_dir=config['Dataset']['movie_dir'], 
                        video_dir=config['Dataset']['video_dir'], 
                        cc_dict_path=config['Dataset']['base_path'],
                        video_list_path=config['Dataset']['base_path'], 
                        action_dict_path='')
    

def display_capture_settings_menu():
    settings_filename = 'capsettings.p'
    #Load previous settings
    if os.path.isfile(settings_filename):
        settings = pickle.load(open(settings_filename, 'rb'))
    else:
        #Default values ['base_path', 'output_path','video_dir','movie_dir']
        settings = VASettings(base_path="/Users/zal/CMU/Fall2015/HCMMML/FinalProject/Dataset/MontrealVideoAnnotationDataset/DVDtranscription",\
                            output_path="/Users/zal/CMU/Fall2015/HCMMML/FinalProject/Dataset/MontrealVideoAnnotationDataset/DVDTranscriptionKeyFrames",\
                            movie_dir='THE_VOW',\
                            video_dir="video",\
                            cc_dict_path='/Users/zal/CMU/Fall2015/HCMMML/FinalProject/Repository/DataProcessing/all_captions_dict.p')
    
    #Ask for changes or leave default
    print 'Setting up the frame grabber, leave the entry empty if you would like to work with default value.'
    print ''
    #BASE PATH
    inText = raw_input("DATASET PATH\n[ %s ]:\n"%(settings.base_path))
    if len(inText) > 0:
        settings.base_path = inText
    #OUTPUT PATH
    inText = raw_input("OUTPUT PATH\n[ %s ]:\n"%(settings.output_path))
    if len(inText) > 0:
        settings.output_path = inText
    #CAPTIONS DICTIONARY
    inText = raw_input("CAPTIONS DICTIONARY\n[ %s ]:\n"%(settings.cc_dict_path))
    if len(inText) > 0:
        settings = settings.cc_dict_path = inText
    #VIDEO DIR
    inText = raw_input("VIDEOS' DIRECTORY\n[ %s ]:\n"%(settings.video_dir))
    if len(inText) > 0:
        settings.video_dir = inText
    #MOVIES DIR
    inText = raw_input("MOVIE DIRECTORY\n[ %s ]:"%(settings.movie_dir))
    if len(inText) > 0:
        settings.movie_dir = inText
    
    # Save current settings
    pickle.dump(settings, open(settings_filename, 'wb'))
    
    return settings

def display_annotate_settings_menu():
    settings_filename = 'annosettings.p'
    #Load previous settings
    if os.path.isfile(settings_filename):
        settings = pickle.load(open(settings_filename, 'rb'))
    else:
        #Default values
        settings = VASettings(base_path='/Users/zal/CMU/Fall2015/HCMMML/FinalProject/Dataset/MontrealVideoAnnotationDataset/DVDtranscription/',\
                            video_list_path="/Users/zal/CMU/Fall2015/HCMMML/FinalProject/Repository/DataProcessing/actions_video_list.txt",\
                            output_path="/Users/zal/CMU/Fall2015/HCMMML/FinalProject/Repository/DataProcessing/video_action_annotations.csv",\
                            cc_dict_path='/Users/zal/CMU/Fall2015/HCMMML/FinalProject/Repository/DataProcessing/all_captions_dict.p',\
                            action_dict_path='/Users/zal/CMU/Fall2015/HCMMML/FinalProject/Repository/DataProcessing/all_video_action_dict.p')
    
    #Ask for changes or leave default
    print 'Setting up the video annotator, leave the entry empty if you would like to work with the default value.'
    #BASE PATH
    inText = raw_input("DATASET PATH\n[ %s ]:\n"%(settings.base_path))
    if len(inText) > 0:
        settings.base_path = inText
    #VIDEO LIST FILE
    inText = raw_input("VIDEO LIST FILE\n[ %s ]:\n"%(settings.video_list_path))
    if len(inText) > 0:
        settings.video_list_path = inText
    #OUTPUT FILE
    inText = raw_input("OUTPUT FILE\n[ %s ]:\n"%(settings.output_path))
    if len(inText) > 0:
        settings.output_path = inText
    #CAPTIONS DICTIONARY
    inText = raw_input("CAPTIONS DICTIONARY\n[ %s ]:\n"%(settings.cc_dict_path))
    if len(inText) > 0:
        settings.cc_dict_path = inText
    #ACTIONS DICTIONARY
    inText = raw_input("ACTIONS DICTIONARY\n[ %s ]:\n"%(settings.action_dict_path))
    if len(inText) > 0:
        settings.action_dict_path = inText
    
    # Save current settings
    pickle.dump(settings, open(settings_filename, 'wb'))
    
    return settings
    

if __name__ == '__main__': 
    '''
    Main entry point of the program
    '''
    app_mode = '0'
    while app_mode != '1' and app_mode != '2':
        app_mode = raw_input('Select the annotation mode:\n(1) Capture Frame \n(2) Annotate time\n')
        if app_mode != '1' and app_mode != '2':
            print 'Please select an option between 1 or 2.'
    
    if app_mode == '1':
        settings = display_capture_settings_menu()
        capture_movie_frames(settings.base_path, settings.output_path, settings.video_dir, settings.movie_dir, settings.cc_dict_path)
    elif app_mode == '2':
        settings = display_annotate_settings_menu()
        annotate_movie_times(settings.base_path, settings.video_list_path, settings.cc_dict_path, settings.output_path, settings.action_dict_path)
    
    print 'Session ended'