import re
from sqlalchemy import *

ID_MVAD = 'MVAD'
ID_MPII = 'MPII'

class MovieName:
    def __init__(self):
        self.name = ''
        self.dataset = ''
        self.dataset_name = ''

def build_movie_names(uniq_names):
    mpiiRegex = re.compile(r'\d\d\d\d_(.+)')
    movie_name_list = []
    
    for dataset_name in uniq_names:
        mo1 = mpiiRegex.search(dataset_name)
        if mo1 is not None:
            # It is an MPII name
            name_only = mo1.group(1).upper()
            movie_name  = MovieName()
            movie_name.name = name_only.replace('_', ' ')
            movie_name.dataset_name = dataset_name
            movie_name.dataset = ID_MPII
            movie_name_list.append(movie_name)
        else:
            # It is an M-VAD name
            movie_name  = MovieName()
            movie_name.name = dataset_name.replace('_', ' ')
            movie_name.dataset_name = dataset_name
            movie_name.dataset = ID_MVAD
            movie_name_list.append(movie_name)
    
    return movie_name_list

def get_unique_names_from_db():
    engine = create_engine('mysql://annotator:multicomp@atlas4.multicomp.cs.cmu.edu/annodb')
    db_res = engine.execute('SELECT DISTINCT movie FROM allvideos')
    unique_names = [row[0] for row in db_res]
    
    return unique_names

def store_in_db(movie_names):
    engine = create_engine('mysql://annotator:multicomp@atlas4.multicomp.cs.cmu.edu/annodb')
    
    for movie_name in movie_names:
        query = "INSERT INTO movies (name, dataset_name, dataset) VALUES ('%s','%s','%s')"%(movie_name.name, movie_name.dataset_name, movie_name.dataset)
        db_res = engine.execute(query)

def main():
    uniq_names = get_unique_names_from_db()
    movie_names = build_movie_names(uniq_names)
    store_in_db(movie_names)

if __name__=='__main__':
    main()