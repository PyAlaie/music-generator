import os
import pathlib

BASE_DIR = pathlib.Path(__file__).parent
DATA_PATH = BASE_DIR / 'data'


class Crawl:
    base_url = 'https://www.midiworld.com/'
    composers_url = 'composers.htm'


class MidiFiles:
    database = DATA_PATH / 'db.csv'
    raw_midi_files = DATA_PATH / 'midi'
    encoded_files = DATA_PATH / 'encoded'
    preprocessed_csv_files = DATA_PATH / 'preprocessed'
    temp_space = DATA_PATH / 'temp'
    log_space = DATA_PATH / 'log'
    weights_path = DATA_PATH / 'models'
    generated_csv_path = DATA_PATH / 'generated_csv'

