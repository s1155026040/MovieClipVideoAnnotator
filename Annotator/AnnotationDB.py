import sys
from sqlalchemy import * #requires MySQLdb package

class Annotation():
    def __init__(self):
        self.file_name = ''
        self.start_frame = -1
        self.end_frame = -1
        self.action = ''
        self.caption = ''
        self.user_id = -1
        self.status = 0 #0: if skipped
        
class AnnotationTask():
    def __init__(self):
        self.id = -1
        self.captionid = -1
        self.text = ''
        self.video_name = ''
        self.video_path = ''
        self.action = ''
        self.movie = ''
        self.dataset = ''
        self.status = -1
        self.batch_id = -1

class Video():
    def __init__(self):
        self.video_path = ''
        self.dataset = ''
        self.movie = ''
        self.length = -1
        self.caption = ''

class AnnotationDB:
    def __init__(self):
        self.engine = None
        self.metadata = MetaData()
    
    def init(self, host, username, password, db_name):
        engine_desc = 'mysql://%s:%s@%s/%s'%(username, password, host, db_name)
        try:
            self.engine = create_engine(engine_desc)
            self.metadata.reflect(self.engine)
        except:
            print "Unexpected error:", sys.exc_info()[0]
            return False
        return True
    
    # USERS table ===============================================================
    def get_all_users(self):
        result = self.engine.execute('select user_id, name from users')
        users = []
        for row in result:
            users.append((row['user_id'], row['name']))
        return users
    
    def insert_user(self, name):
        self.engine.execute('insert into users (name) values (\'%s\')'%name)
    
    # ANNOTATIONS table =========================================================
    def insert_annotation(self, annotation):
        annotations = Table('annotations', self.metadata)
        insert = annotations.insert()
        conn = self.engine.connect()
        result = conn.execute(insert, video_file_name=annotation.file_name,
                              start_frame = annotation.start_frame,
                              end_frame = annotation.end_frame,
                              action = annotation.action,
                              caption = annotation.caption,
                              user_id = annotation.user_id,
                              status = annotation.status)
    
    # ALLVIDEOS table ===========================================================
    def insert_video(self, video):
        videos = Table('allvideos', self.metadata)
        insert = videos.insert()
        conn = self.engine.connect()
        result = conn.execute(insert, video_path = video.video_path,
                              movie = video.movie,
                              dataset = video.dataset,
                              length = video.length,
                              caption = video.caption)
    
    # ANNOTATIONTASK table ======================================================
    def get_annotask_list(self, batch_id):
        annotask = Table('annotationtask', self.metadata)
        sel_stmt = select([annotask.c.id, annotask.c.captionid, annotask.c.text, annotask.c.video_name, annotask.c.video_path, annotask.c.action, annotask.c.action, \
                           annotask.c.movie, annotask.c.dataset, annotask.c.status, annotask.c.batch_id]).\
                        where(annotask.c.batch_id==batch_id)
        rp = self.engine.execute(sel_stmt)
        annotask_list = []
        for row in rp:
            new_task = AnnotationTask()
            new_task.id = row.id
            new_task.captionid = row.captionid
            new_task.text = row.text
            new_task.video_name = row.video_name
            new_task.video_path = row.video_path
            new_task.action = row.action
            new_task.movie = row.movie
            new_task.dataset = row.dataset
            new_task.status = row.status
            new_task.batch_id = row.batch_id
            annotask_list.append(new_task)
        
        annotask_list.sort(key=lambda x: x.id)        
        return annotask_list
    
    def get_annotask_idlist(self, batch_id):
        annotask = Table('annotationtask', self.metadata)
        sel_stmt = select([annotask.c.id]).where(annotask.c.batch_id==batch_id)
        rp = self.engine.execute(sel_stmt)
        id_list = [record.id for record in rp]
        return id_list

    def get_annotation_task(self, anno_task_id):
        result = self.engine.execute('select * from annotationtask where id=%d'%(anno_task_id))
        anno_task = AnnotationTask()
        for item in result:
            anno_task.id = int(item['id'])
            anno_task.captionid = int(item['captionid'])
            anno_task.text = item['text']
            anno_task.video_name = item['video_name']
            anno_task.video_path = item['video_path']
            anno_task.action = item['action']
            anno_task.movie = item['movie']
            anno_task.dataset = item['dataset']
            anno_task.status = int(item['status'])
            anno_task.batch_id = int(item['batch_id'])
        return anno_task

    # BATCHES table ==========================================================
    def insert_batch(self, batch_id, num_times, user_list):
        batches = Table('batches', self.metadata)
        ins_stmt = batches.insert().values(
                    id=batch_id,
                    num_times=num_times,
                    user_register=user_list
                    )
    
    def increase_batch(self, batch_id, user_id):
        batches = Table('batches', self.metadata)
        select_stmt = select([batches.c.num_times, batches.c.user_register]).\
                where(batches.c.id==batch_id)
        rp = self.engine.execute(select_stmt)
        record = rp.first()
        
        increased_times = record.num_times + 1
        increased_register = record.user_register + ' %d'%(user_id)
        increased_register = increased_register.strip()
        
        update_stmt = update(batches).\
                       where(batches.c.id==batch_id).\
                       values(num_times=increased_times,
                              user_register=increased_register)
        
        self.engine.execute(update_stmt)
        
    def get_batch_numtimes(self, batch_id):
        batches = Table('batches', self.metadata)
        stmt = select([batches.c.num_times]).where(batches.c.id==batch_id)
        rp = self.engine.execute(stmt)
        record = rp.first()
        return record.num_times
    
    def get_batch_userregister(self, batch_id):
        batches = Table('batches', self.metadata)
        stmt = select([batches.c.user_register]).where(batches.c.id==batch_id)
        rp = self.engine.execute(stmt)
        record = rp.first()
        return record.user_register    
        
    # USERSTASK table ==========================================================
    def get_cur_batchid(self, user_id):
        userstask = Table('userstask', self.metadata)
        stmt = select([userstask.c.batch_id]).where(userstask.c.user_id==user_id)
        rp = self.engine.execute(stmt)
        record = rp.first()
        return record.batch_id
    
    def get_next_batchid(self):
        userstask = Table('userstask', self.metadata)
        stmt = select([userstask.c.batch_id])
        rp = self.engine.execute(stmt)
        all_batch_id = [row.batch_id for row in rp]
        return max(all_batch_id) + 1
    
    def get_userstask_listsize(self, user_id):
        result = self.engine.execute('select list_size from userstask where user_id=%d'%(user_id))
        list_size = 0
        for row in result:
            list_size = row['list_size']
        return list_size

    def get_userstask_lastpos(self, user_id):
        userstask = Table('userstask', self.metadata)
        stmt = select([userstask.c.last_pos]).where(userstask.c.user_id==user_id)
        rp = self.engine.execute(stmt)
        record = rp.first()
        return record.last_pos
    
    def get_userstask_batchid(self, user_id):
        userstask = Table('userstask', self.metadata)
        stmt = select([userstask.c.batch_id]).where(userstask.c.user_id==user_id)
        rp = self.engine.execute(stmt)
        record = rp.first()
        return record.batch_id
    
    def get_userstask_batchid_list(self):
        userstask = Table('userstask', self.metadata)
        stmt = select([userstask.c.batch_id])
        rp = self.engine.execute(stmt)
        batch_id_list = [row.batch_id for row in rp]
        return batch_id_list
    
    def update_userstask_lastpos(self, user_id, pos):
        userstask = Table('userstask', self.metadata)
        stmt = update(userstask).where(userstask.c.user_id==user_id).values(last_pos=pos)
        self.engine.execute(stmt)
        
    def update_userstask_taskid(self, user_id, task_id):
        users = Table('userstask', self.metadata)
        stmt = update(users).where(users.c.user_id==user_id).values(cur_task_id=task_id)
        self.engine.execute(stmt)
    
    def update_userstask_with_newtask(self, user_id, list_size, batch_id):
        userstask = Table('userstask', self.metadata)
        stmt = update(userstask).\
            where(userstask.c.user_id==user_id).\
            values(list_size=list_size,
                   batch_id=batch_id,
                   last_pos=-1)
        self.engine.execute(stmt)
        
def test():
    db = AnnotationDB()
    if not db.init('atlas4.multicomp.cs.cmu.edu', 'annotator', 'multicomp', 'annodb'):
        print 'Could not connect to DB'
        sys.exit(-1)
    
    # Test users
    users = db.get_all_users()
    print users[0]    
    print db.get_cur_taskid(users[0][0])
    print db.get_next_taskid()
    db.update_userstask_taskid(1,0)    
    
    #Test batches 
    db.increase_batch(0, 2)
    
    #Test annotasklist
    batch_list = db.get_annotask_list(2)
    print ' '.join([str(caption.id)for caption in batch_list])
    
    #Test annotation
    #annotation = Annotation()
    #annotation.file_name = '21_JUMP_STREET/video/21_JUMP_STREET_DV520.avi'
    #annotation.start_frame = 10
    #annotation.end_frame = 30
    #annotation.action = 'jump'
    #annotation.caption = 'SOMEONE jumped out of the roof'
    #annotation.user_id = 2
    #db.insert_annotation(annotation)