import os

_current_file = os.path.abspath(__file__)
BASEDIR = os.path.dirname(_current_file)

DATA_PATH = BASEDIR + '/data'

class Crawl:
    base_url = 'https://www.midiworld.com/'
    composers_url = 'composers.htm'

class MidiFiles:
    database = DATA_PATH + '/db.csv'
    raw_midi_files = DATA_PATH + '/midi'
    raw_csv_files = DATA_PATH + '/csv'
    preprocessed_csv_files = DATA_PATH + '/preprocessed'
    temp_space = DATA_PATH + '/temp'
    log_space = DATA_PATH + '/log'