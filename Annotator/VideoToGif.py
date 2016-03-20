# 
# This package generates animated GIF files from a sequence of images
# It is also capable of converting videos to animated GIFs
#
# Requirements: imageio
#               moviepy
#               opencv
#
# Carnegie Mellon University
# author: Salvador Medina
# last update: 2016-02-23
#
# Name conventions: filename is the name of a file with extension
#                   directory is the full path of a directory
#                   path is the full path to a file 

from __future__ import division
import cv2
import os
import re
import glob
from imageio import imread
import moviepy.editor as mpy

def extract_video_frames(video_path):
    '''
    Extracts the frames from the given video file
    RETURNS: list with ALL the video frames
    '''
    if not os.path.isfile(video_path):
        print 'ERROR: could not find video file'
        return 0
    
    frame_list = []
    vidcap = cv2.VideoCapture(video_path)
    if not vidcap.isOpened():
        print 'ERROR: could not open video file'
        return 0
    
    ret, fr = vidcap.read()
    
    while ret:
        
        frame_list.append(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))
        ret, fr = vidcap.read()    
        
    return frame_list

def create_gif(img_list, duration):
    '''
    Generates an animated gif from a sequence based on the duration
    Returns a MoviePy animation object
    '''
    fps = int(round(len(img_list)/duration))
    def make_frame(t):
        '''
        Auxiliary function required by MoviePy which extracts the image
        to be appendeded to the animation at time *t* in [s]
        '''
        cur_frame = int(round(t*fps))
        # Make sure that the queried frame is in the list
        if cur_frame < len(img_list):
            return img_list[cur_frame]
        # Otherwise return the last frame
        return img_list[-1]    
    
    animation = mpy.VideoClip(make_frame, duration=duration) 
    return animation
    

def video_to_gif(video_path, gif_path, start_frame=1, end_frame=float('inf'), video_fps=24):
    '''
    Converts a video to an animated gif
    The source video codecs must be installed in order to extract frames
    '''
    video_frame_list = extract_video_frames(video_path) # image list to be animated
    total_frames = len(video_frame_list)
    if end_frame > totalFrames:
        end_frame = totalFrames
    if end_frame - start_frame != totalFrames:
        duration = (end_frame-start_frame) / video_fps        # duration in [s]
        animation = create_gif(video_frame_list[start_frame:end_frame+1], duration)  # this call is the core of the function
        animation.write_gif(gif_path, fps=video_fps)        # save to file        
    else:
        duration = len(video_frame_list) / video_fps        # duration in [s]
        animation = create_gif(video_frame_list, duration)  # this call is the core of the function
        animation.write_gif(gif_path, fps=video_fps)        # save to file