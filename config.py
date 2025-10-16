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
    preprocessed_csv_files = DATA_PATH / 'preprocessed'
    temp_space = DATA_PATH / 'temp'
    log_space = DATA_PATH / 'log'
    weights_path = DATA_PATH / 'models'
    generated_csv_path = DATA_PATH / 'generated_csv'


class LstmParameters:
    seq_len = 50
    num_features = 25

    batch_size = 128
    epochs = 30

    final_model_path = DATA_PATH / 'final_model.weights.h5'