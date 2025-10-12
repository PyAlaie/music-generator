import config, os, tqdm, random, inspect, pickle, shutil
from mido import MidiFile, MidiTrack, merge_tracks
import py_midicsv as pm
from midi2audio import FluidSynth

class BackToMidi:
    def __init__(self, try_to_load_progress=True):
        self.generated_csv_path = config.MidiFiles.generated_csv_path
        self.preprocess_id = f"{self.__class__.__name__}_{self.generate_random_string(6)}"

        if try_to_load_progress and self.load_progress():
            pass
        else:
            self.preprocess_id = f"{self.__class__.__name__}_{self.generate_random_string(6)}"
            self.temp_space = config.MidiFiles.temp_space / self.preprocess_id
            self.progress = {}

    def generate_random_string(self, length=16):
        chars = [chr(i) for i in range(97,123)]
        chars = ''.join(chars)
        chars += chars.upper()

        random_string = [random.choice(chars) for i in range(length)]
        
        return ''.join(random_string)

    def add_headers_and_cols(self, try_to_load=True):
        if try_to_load:
            func_name = inspect.currentframe().f_code.co_name
            if func_name in self.progress:
                print(f"Loaded {func_name} progress!")
                return self.progress[func_name]

        func_id = f"{inspect.currentframe().f_code.co_name}_{self.generate_random_string(6)}"
        output_path = self.temp_space / func_id
        os.makedirs(output_path)

        files = os.listdir(self.generated_csv_path)

        channel = track = "1"
        event = "Note_on_c"
        header = "delta_time,event,channel,pitch,velocity,duration\n"

        for file in tqdm.tqdm(files, desc="Adding headers"):
            with open(self.generated_csv_path / file, 'r') as f:
                lines = f.readlines()

            res = []
            for index, line in enumerate(lines):
                if index == 0: # this is the header
                    res.append(header)
                    continue

                parsed = line.strip().split(',')
                parsed.insert(1, event)
                parsed.insert(2, channel)
                parsed.insert(0, track)

                new_line = ','.join(parsed)

                res.append(new_line + '\n')
            
            with open(output_path / file, "w") as output_file:
                output_file.writelines([i for i in res])
        
        self.progress[inspect.currentframe().f_code.co_name] = func_id
        
        return func_id

    def cumulate_delta_times(self, try_to_load=True, last_pipeline_id=None):
        if try_to_load:
            func_name = inspect.currentframe().f_code.co_name
            if func_name in self.progress:
                print(f"Loaded {func_name} progress!")
                return self.progress[func_name]

        if last_pipeline_id is None:
            raise ValueError("last pipe line is none!")

        files_path = self.temp_space / last_pipeline_id 

        func_id = f"{inspect.currentframe().f_code.co_name}_{self.generate_random_string(6)}"
        output_path = self.temp_space / func_id
        os.makedirs(output_path)

        files = os.listdir(files_path)

        for file in tqdm.tqdm(files, desc="Cumulating delta times"):
            with open(files_path / file, 'r') as f:
                lines = f.readlines()

            res = []
            cumulated_time = 0
            for index, line in enumerate(lines):
                if index == 0:
                    continue
                
                parsed = line.split(',')
                time = int(parsed[1])

                cumulated_time += time
                parsed[1] = str(cumulated_time)
                res.append(','.join(parsed))

            with open(output_path / file, "w") as output_file:
                output_file.writelines([i for i in res])
        
        self.progress[inspect.currentframe().f_code.co_name] = func_id
        
        return func_id

    def unpack_durations(self, try_to_load=True, last_pipeline_id=None):
        if try_to_load:
            func_name = inspect.currentframe().f_code.co_name
            if func_name in self.progress:
                print(f"Loaded {func_name} progress!")
                return self.progress[func_name]

        if last_pipeline_id is None:
            raise ValueError("last pipe line is none!")

        files_path = self.temp_space / last_pipeline_id 

        func_id = f"{inspect.currentframe().f_code.co_name}_{self.generate_random_string(6)}"
        output_path = self.temp_space / func_id
        os.makedirs(output_path)

        files = os.listdir(files_path)

        for file in tqdm.tqdm(files, desc="Unpacknig durations"):
            with open(files_path / file, 'r') as f:
                lines = f.readlines()

            res = []
            for index, line in enumerate(lines):
                parsed = line.strip().split(',')
                time = int(parsed[1])
                duration = int(parsed[-1])

                old_event = parsed[:-1]
                res.append(','.join(old_event) + '\n')

                new_event_time = time+duration
                new_event = f"1,{new_event_time},Note_on_c,1,62,0\n"

                res.append(new_event)

            res.sort(key= lambda x: int(x.split(',')[1]))

            with open(output_path / file, "w") as output_file:
                output_file.writelines([i for i in res])
        
        self.progress[inspect.currentframe().f_code.co_name] = func_id
        
        return func_id
    
    def add_final_headers(self, try_to_load=True, last_pipeline_id=None):
        if try_to_load:
            func_name = inspect.currentframe().f_code.co_name
            if func_name in self.progress:
                print(f"Loaded {func_name} progress!")
                return self.progress[func_name]

        if last_pipeline_id is None:
            raise ValueError("last pipe line is none!")

        files_path = self.temp_space / last_pipeline_id 

        func_id = f"{inspect.currentframe().f_code.co_name}_{self.generate_random_string(6)}"
        output_path = self.temp_space / func_id
        os.makedirs(output_path)

        files = os.listdir(files_path)

        for file in tqdm.tqdm(files, desc="Add final headers"):
            with open(files_path / file, 'r') as f:
                lines = f.readlines()

            last_time = int(lines[-1].split(',')[1])

            header1 = "0,0,Header,0,1,380\n"
            header2 = "1,0,Start_track\n"
            tail1 = f"1,{last_time},End_track\n"
            tail2 = "0,0,End_of_file\n"

            lines.insert(0, header1)
            lines.insert(1, header2)
            lines.append(tail1)
            lines.append(tail2)

            with open(output_path / file, "w") as output_file:
                output_file.writelines([i for i in lines])
        
        self.progress[inspect.currentframe().f_code.co_name] = func_id
        
        return func_id

    def convert_back_to_midi(self, try_to_load=True, last_pipeline_id=None):
        if try_to_load:
            func_name = inspect.currentframe().f_code.co_name
            if func_name in self.progress:
                print(f"Loaded {func_name} progress!")
                return self.progress[func_name]

        if last_pipeline_id is None:
            raise ValueError("last pipe line is none!")

        files_path = self.temp_space / last_pipeline_id 

        func_id = f"{inspect.currentframe().f_code.co_name}_{self.generate_random_string(6)}"
        output_path = self.temp_space / func_id
        os.makedirs(output_path)

        files = os.listdir(files_path)

        for file in tqdm.tqdm(files, desc="Converting to midi"):
            with open(files_path / file, "r") as f:
                lines = f.readlines()

            midi_object = pm.csv_to_midi(lines)
            name = '.'.join(file.split('.')[:-1]) + '.mid'

            with open(output_path / name, "wb") as output_file:
                midi_writer = pm.FileWriter(output_file)
                midi_writer.write(midi_object)
        
        self.progress[inspect.currentframe().f_code.co_name] = func_id

        return func_id
    
    def render_wavs(self, try_to_load=True, last_pipeline_id=None):
        if try_to_load:
            func_name = inspect.currentframe().f_code.co_name
            if func_name in self.progress:
                print(f"Loaded {func_name} progress!")
                return self.progress[func_name]

        if last_pipeline_id is None:
            raise ValueError("last pipe line is none!")

        files_path = self.temp_space / last_pipeline_id 

        func_id = f"{inspect.currentframe().f_code.co_name}_{self.generate_random_string(6)}"
        output_path = self.temp_space / func_id
        os.makedirs(output_path)

        files = os.listdir(files_path)

        fs = FluidSynth()
        for file in tqdm.tqdm(files, desc="Rendering files"):
            name = '.'.join(file.split('.')[:-1]) + '.wav'
            fs.midi_to_audio(files_path / file, output_path / name)
        
        self.progress[inspect.currentframe().f_code.co_name] = func_id

        return func_id

    def save_progress(self, clear_cache=True):
        file_path = self.preprocess_id + '.pkl'

        with open(self.temp_space / file_path, "wb") as file:
            pickle.dump(self.progress, file)

        if clear_cache:
            values = self.progress.values()
            directories = [d for d in os.listdir(self.temp_space) if os.path.isdir(os.path.join(self.temp_space, d))]
            for directory in directories:
                if directory not in values:
                    shutil.rmtree(self.temp_space / directory)

    def load_progress(self):
        progresses = os.listdir(config.MidiFiles.temp_space)
        filtered = [f for f in progresses if f.startswith(self.__class__.__name__)]

        pkl_file = ""
        progress = ""

        if len(filtered) == 0:
            return False
        
        elif len(filtered) == 1:
            progress = filtered[0]
            pkl_file = config.MidiFiles.temp_space / progress / f"{progress}.pkl"
        
        else:
            [print("{i}. {progress}") for i, progress in enumerate(filtered)]
            option = int(input())

            progress = filtered[option]
            pkl_file = config.MidiFiles.temp_space / progress / f"{progress}.pkl"

        
        with open(pkl_file, "rb") as file:
            self.progress = pickle.load(file)
            self.preprocess_id = progress
            self.temp_space = config.MidiFiles.temp_space / self.preprocess_id
        
        print(f"Loaded progress {progress}")

        return True

if __name__ == "__main__":
    backToMidi = BackToMidi()

    func_id = backToMidi.add_headers_and_cols(try_to_load=False)
    func_id = backToMidi.cumulate_delta_times(last_pipeline_id=func_id, try_to_load=False)
    func_id = backToMidi.unpack_durations(last_pipeline_id=func_id, try_to_load=False)
    func_id = backToMidi.add_final_headers(last_pipeline_id=func_id, try_to_load=False)
    func_id = backToMidi.convert_back_to_midi(last_pipeline_id=func_id, try_to_load=False)
    # func_id = backToMidi.render_wavs(last_pipeline_id=func_id, try_to_load=False)
    backToMidi.save_progress()