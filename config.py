import os
import pathlib

BASE_DIR = pathlib.Path(__file__).parent
DATA_PATH = BASE_DIR / 'data'


class Crawl:
    base_url = 'https://www.midiworld.com/'
    composers_url = 'composers.htm'

    STREAM_CHUNK_SIZE = 4096
    

class MidiFiles:
    database = DATA_PATH / 'db.csv'
    raw_midi_files = DATA_PATH / 'midi'
    preprocessed_csv_files = DATA_PATH / 'preprocessed'
    temp_space = DATA_PATH / 'temp'
    log_space = DATA_PATH / 'log'
    weights_path = DATA_PATH / 'models'
    generated_csv_path = DATA_PATH / 'generated_csv'


class LstmParameters:
    transpose_offset = 12 # Should be a number between 1 and 12

    seq_len = 50
    num_features = 26

    batch_size = 256
    epochs = 30

    final_model_path = DATA_PATH / 'final_model.weights.h5'