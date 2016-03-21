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
            self.metadata.reflect(self.engine, only=['users', 'annotations', 'videos'])
        except:
            print "Unexpected error:", sys.exc_info()[0]
            return False
        return True
    
    def get_users(self):
        result = self.engine.execute('select user_id, name from users')
        users = []
        for row in result:
            users.append((row['user_id'], row['name']))
        return users
    
    def insert_annotation(self, annotation):
        annotations = Table('annotations', self.metadata)
        insert = annotations.insert()
        conn = self.engine.connect()
        result = conn.execute(insert, video_file_name=annotation.file_name,
                              start_frame = annotation.start_frame,
                              end_frame = annotation.end_frame,
                              action = annotation.action,
                              caption = annotation.caption,
                              user_id = annotation.user_id)
    
    def insert_video(self, video):
        videos = Table('videos', self.metadata)
        insert = videos.insert()
        conn = self.engine.connect()
        result = conn.execute(insert, video_path = video.video_path,
                              movie = video.movie,
                              dataset = video.dataset,
                              length = video.length,
                              caption = video.caption)
        

def test():
    db = AnnotationDB()
    if not db.init('atlas4.multicomp.cs.cmu.edu', 'annotator', 'multicomp', 'annodb'):
        print 'Could not connect to DB'
        sys.exit(-1)
    users = db.get_users()
    print users[0]
    
    annotation = Annotation()
    annotation.file_name = '21_JUMP_STREET/video/21_JUMP_STREET_DV520.avi'
    annotation.start_frame = 10
    annotation.end_frame = 30
    annotation.action = 'jump'
    annotation.caption = 'SOMEONE jumped out of the roof'
    annotation.user_id = 2
    db.insert_annotation(annotation)
