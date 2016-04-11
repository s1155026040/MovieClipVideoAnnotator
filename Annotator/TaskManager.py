import os
import sys
from AnnotationDB import *


LINT_SEPARATOR = ' '

class TaskManager:
    def __init__(self, user_id, db):
        self.uid = user_id
        self.db = db
        
    def is_cur_task_complete(self):
        cur_tasklist_size = self.db.get_userstask_listsize(self.uid)
        last_task_pos = self.db.get_userstask_lastpos(self.uid)
        return last_task_pos >= (cur_tasklist_size-1)
    
    def set_cur_task_as_complete(self):
        batch_id = self.db.get_userstask_batchid(self.uid)
        self.db.increase_batch(batch_id, self.uid)
    
    def get_next_batchid(self):
        #Get the values
        batch_list = self.db.get_userstask_batchid_list()
        max_batch_id = max(batch_list)        
    
        # If it appears twice or more, then get a larger one
        if batch_list.count(max_batch_id) > 1:
            return max_batch_id + 1
        
        # if it is already being annotated and someone has already annotated it
        # move to the next one
        max_batch_times_annotated = self.db.get_batch_numtimes(max_batch_id)
        if max_batch_times_annotated >= 1:
            return max_batch_id + 1
        
        # if I have already annotated it
        max_batch_userreg = self.str_to_lint(self.db.get_batch_userregister(max_batch_id))
        if self.uid in max_batch_userreg:
            return max_batch_id + 1
        
        # everything seems to be ok, set up the max batch id
        return max_batch_id
        
    def setup_next_task(self):
        ''' Updates the annotation task with the new batch id'''
        
        #Determine the next batch id
        next_batch_id = self.get_next_batchid()
        
        #Update the user's task table
        next_batch_cid_list = self.db.get_annotask_idlist(next_batch_id)
        next_batch_cid_list_str = self.lint_to_str(next_batch_cid_list)
        next_batch_size = len(next_batch_cid_list)
        self.db.update_userstask_with_newtask(self.uid, next_batch_size, next_batch_id)
        
    def terminate_cur_task(self):
        '''Registers the current annotation task as finished and sets up the db for the next annotation task'''
        #registers the current task as complete
        self.set_cur_task_as_complete()
        
        #sets up the next task batch to be completed by the user
        self.setup_next_task()
        
    def update_annotask_pos(self, new_pos):
        '''Updates the last annotated possition'''
        self.db.update_userstask_lastpos(self.uid, new_pos)
    
    def get_last_pos(self):
        return self.db.get_userstask_lastpos(self.uid)
    
    def get_annotation_list(self):
        ''' Returns a list of AnnotationTask objects and the current pos of the annotation batch'''
        annotask_list = []
        last_pos = -1
        
        cur_batchid = self.db.get_cur_batchid(self.uid)
        annotask_list = self.db.get_annotask_list(cur_batchid)
        last_pos = self.db.get_userstask_lastpos(self.uid)
            
        return annotask_list, last_pos
    
    # Util functions
    def lint_to_str(self, lint):
        ''' Converts a list of ints to string separated by space '''
        return LINT_SEPARATOR.join(map(str, lint))
    
    def str_to_lint(self, strint):
        ''' Converts a string of list of ints into list of ints '''
        strint = strint.strip()
        if len(strint) < 1:
            return []
        return map(int, strint.split(LINT_SEPARATOR))

def test():
    db = AnnotationDB()
    if not db.init('atlas4.multicomp.cs.cmu.edu', 'annotator', 'multicomp', 'annodb'):
        print 'Could not connect to DB'
        sys.exit(-1)    

    target_uid = 2
    taskMgr = TaskManager(target_uid, db)
    
    #for uid in range(1,7):
    #    taskMgr.uid = uid
    #    taskMgr.setup_next_task()
    
    #taskMgr.terminate_cur_task()
    
    #print taskMgr.is_cur_task_complete()
    
    #annotation_list, last_pos = taskMgr.get_annotation_list()
    #for item in annotation_list:
    #    print item.video_path
    #print len(annotation_list), last_pos
    #print annotation_list[0].text
    #taskMgr.update_annotask_pos(last_pos+10)
    #print taskMgr.get_last_pos()
    

test()
    