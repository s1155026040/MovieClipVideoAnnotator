#!/usr/bin/env python
# 
# This is a set of tools that process a video and extracts the
# keyfames based on different criteria such as random sampling
# color histogram and motion detection
#
# Carnegie Mellon University
# author: Salvador Medina
# last update: 2016-03-19
#

from __future__ import division
import cv2

def random_extract(video_path, num_frames):
    total_frames = get_total_frames(video_path)
    span = int( total_frames / num_frames)
    frame_idx = range(0,total_frames,span)
    pass

def color_extract(video_path, num_frames):
    pass

def motion_extract(video_path, num_frames):
    pass