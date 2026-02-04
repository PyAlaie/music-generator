import config, os, tqdm, random, inspect, pickle, shutil
from mido import MidiFile, MidiTrack, merge_tracks
import py_midicsv as pm

class Preprocess:
    def __init__(self, try_to_load_progress=True):
        self.raw_midis_path = config.MidiFiles.raw_midi_files
        self.try_to_load_progress = try_to_load_progress

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

    def merge_midi_tracks(self, try_to_load=True, **kwargs):
        if try_to_load:
            func_name = inspect.currentframe().f_code.co_name
            if func_name in self.progress:
                print(f"Loaded {func_name} progress!")
                return self.progress[func_name]

        midi_files = os.listdir(self.raw_midis_path)

        func_id = f"{inspect.currentframe().f_code.co_name}_{self.generate_random_string(6)}"
        output_path = self.temp_space / func_id
        os.makedirs(output_path)

        logs = []

        def is_single_piano(mid:MidiFile):
            instruments = set()

            for track in mid.tracks:
                for msg in track:
                    if msg.type == 'program_change':
                        instruments.add(msg.program)

            return len(instruments) == 1 and (0 <= list(instruments)[0] <= 7)

        for midi_file in tqdm.tqdm(midi_files, desc="Merging Tracks"):
            try:
                mid = MidiFile(self.raw_midis_path / midi_file)

                if not is_single_piano(mid):
                    raise ValueError("File is not a single piano music!")
                
                merged = merge_tracks(mid.tracks)
                mid.tracks = [merged] 
                mid.save(output_path / midi_file)
            
            except Exception as e:
                log = f"File {midi_file} had some error: {e}"
                logs.append(log)

        with open(config.MidiFiles.log_space / func_id, 'w') as file:
            file.writelines([i + '\n' for i in logs])

        self.progress[inspect.currentframe().f_code.co_name] = func_id
        
        return func_id

    def convert_midis_to_csv(self, last_pipeline_id=None, try_to_load=True):
        if try_to_load:
            func_name = inspect.currentframe().f_code.co_name
            if func_name in self.progress:
                print(f"Loaded {func_name} progress!")
                return self.progress[func_name]

        func_id = f"{inspect.currentframe().f_code.co_name}_{self.generate_random_string(6)}"
        output_path = self.temp_space / func_id
        os.makedirs(output_path)

        files_path = config.MidiFiles.raw_midi_files

        if last_pipeline_id is not None:
            files_path = self.temp_space / last_pipeline_id 

        files = os.listdir(files_path)

        csv_files = []
        names = []

        logs = []
        for file in tqdm.tqdm(files, desc="Converting"):
            try:
                csv_file = pm.midi_to_csv(str(files_path / file))
                csv_files.append(csv_file)

                name = file.split('.')[:-1]
                name = ''.join(name)
                names.append(name)

            except Exception as e:
                logs.append(file)
                print(e)

        for file, name in tqdm.tqdm(zip(csv_files, names), desc="Wrting"):
            with open(str(output_path / name) + ".csv", "w") as f:
                f.writelines(file)
        
        print("Exceptions:", len(logs))
        with open(config.MidiFiles.log_space / func_id, "w") as f:
            f.writelines([i + '\n' for i in logs])

        self.progress[inspect.currentframe().f_code.co_name] = func_id
        
        return func_id
    
    def remove_meta_data(self, last_pipeline_id=None, try_to_load=True):
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

        csv_files = os.listdir(files_path)
        meta_data_tags = ["Control_c", "Pitch_bend_c", "Program_c", "Poly_aftertouch_c", "Channel_aftertouch_c", "System_exclusive", "Channel_prefix", "Sequencer_specific", "MIDI_port", "Title_t", "Copyright_t", "Instrument_name_t", "Marker_t", "Cue_point_t", "Lyric_t", "Text_t", "Key_signature", "Time_signature", "SMPTE_offset"]

        for file_name in tqdm.tqdm(csv_files, desc="Removing metadata"):
            with open(files_path / file_name, 'r') as input_file:
                lines = input_file.readlines()
            
            filtered_lines = []
            for line in lines:
                line = line.split(',')
                line = [l.strip() for l in line]
                
                if line[2] not in meta_data_tags: # if it is metadata
                    filtered_lines.append(','.join(line))
            
            with open(output_path / file_name, "w") as output_file:
                output_file.writelines([i + '\n' for i in filtered_lines])
        
        self.progress[inspect.currentframe().f_code.co_name] = func_id
        
        return func_id

    def preprocess_notes(self, last_pipeline_id=None, try_to_load=True):
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

        tag = "Note_off_c"
        replace_with = "Note_on_c"

        csv_files = os.listdir(files_path)

        for file_name in tqdm.tqdm(csv_files, desc="Preprocessing notes"):
            with open(files_path / file_name, 'r') as input_file:
                lines = input_file.readlines()
            
            filtered_lines = []
            for line in lines:
                line = line.split(',')
                line = [l.strip() for l in line]

                if line[2] == tag:
                    line[2] = replace_with
                    line[-1] = '0'
                
                filtered_lines.append(','.join(line))

            with open(output_path / file_name, "w") as output_file:
                output_file.writelines([i + '\n' for i in filtered_lines])
        
        self.progress[inspect.currentframe().f_code.co_name] = func_id
        
        return func_id

    def scale_timings(self, last_pipeline_id=None, try_to_load=True, t_new=380, s_new=500000):
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

        csv_files = os.listdir(files_path)

        for file_name in tqdm.tqdm(csv_files, desc="Scaling the ticks"):
            with open(files_path / file_name, 'r') as input_file:
                lines = input_file.readlines()
            
            header = lines.pop(0)

            header = header.split(',')
            t_old = int(header[5])
            current_tempo = 500_000

            last_tick_old = 0
            last_tick_new = 0

            res = [f"0,0,Header,0,1,{t_new}\n"]
            for line in lines:
                line = line.split(',')

                tick_old = int(line[1])
                delta_old = tick_old - last_tick_old  # ticks since previous event

                # Convert delta using current tempo
                # old delta (ticks) → microseconds → new delta (ticks)
                delta_us = delta_old * (current_tempo / t_old)
                delta_new = round(delta_us * (t_new / s_new))

                # Update tick
                tick_new = last_tick_new + delta_new
                line[1] = str(tick_new)

                # If this event is a tempo change, update current_tempo
                if line[2] == "Tempo":
                    current_tempo = int(line[3])  # use its tempo going forward

                # Update state
                last_tick_old = tick_old
                last_tick_new = tick_new

                if line[2] != "Tempo":
                    res.append(','.join(line))

            # fixing the end of file
            line = res[-1]
            line = line.split(',')
            line[1] = '0'
            res[-1] = ','.join(line)
            
            with open(output_path / file_name, "w") as output_file:
                output_file.writelines([i for i in res])

        self.progress[inspect.currentframe().f_code.co_name] = func_id
        
        return func_id

    def calculate_note_durations(self, last_pipeline_id=None, try_to_load=True):
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

        csv_files = os.listdir(files_path)

        for file_name in tqdm.tqdm(csv_files, desc="Calculating durations"):
            with open(files_path / file_name, 'r') as input_file:
                lines = input_file.readlines()
            
            res = []
            for index, line in enumerate(lines):
                parsed = line.strip().split(',')
                event = parsed[2]

                if event != "Note_on_c": 
                    res.append(line)
                    continue

                note = parsed[4]
                velocity = parsed[5]
                time = int(parsed[1])

                if velocity == '0':
                    continue
                
                # trying to see when the note goes off
                duration = 0
                for new_line in lines[index+1:]:
                    new_parsed = new_line.strip().split(',')
                    
                    new_event = new_parsed[2]
                    if new_event != "Note_on_c": 
                        continue

                    new_note = new_parsed[4]
                    new_velocity = new_parsed[5]

                    if new_note == note and new_velocity == '0':
                        new_time = int(new_parsed[1])
                        duration = new_time - time
                        break
                
                parsed.append(str(duration))

                res.append(','.join(parsed) + '\n')
            
            with open(output_path / file_name, "w") as output_file:
                output_file.writelines([i for i in res])

        self.progress[inspect.currentframe().f_code.co_name] = func_id
        
        return func_id

    def calculate_delta_times(self, last_pipeline_id=None, try_to_load=True):
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

        csv_files = os.listdir(files_path)

        for file_name in tqdm.tqdm(csv_files, desc="Calculating delta times"):
            with open(files_path / file_name, 'r') as input_file:
                lines = input_file.readlines()
            
            res = []
            last_time = 0
            for line in lines:
                parsed = line.split(',')
                time = int(parsed[1])

                delta = time - last_time
                parsed[1] = str(delta)
                last_time = time

                res.append(','.join(parsed))
            
            with open(output_path / file_name, "w") as output_file:
                output_file.writelines([i for i in res])

        self.progress[inspect.currentframe().f_code.co_name] = func_id
        
        return func_id

    def finalize_preprocess(self, last_pipeline_id=None, try_to_load=True):
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

        csv_files = os.listdir(files_path)

        excluding_tags = ["Header", "Start_track", "End_of_file", "End_track"]

        for file_name in tqdm.tqdm(csv_files, desc="Finalizing"):
            with open(files_path / file_name, 'r') as input_file:
                lines = input_file.readlines()
            
            header = ["delta_time", "pitch", "duration"] 
            header = ','.join(header)

            res = [header]
            for line in lines:
                line = line.strip().split(',')

                if line[2].strip() in excluding_tags:
                    continue

                del line[5] # velocity
                del line[3] # channel
                del line[2] # event
                del line[0] # track

                res.append(','.join(line))
            
            with open(output_path / file_name, "w") as output_file:
                output_file.writelines([i+'\n' for i in res])

            input_file.close()

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

    def turn_in(self, last_pipeline_id=None):
        if last_pipeline_id is None:
            raise ValueError("last pipe line is none!")

        files_path = self.temp_space / last_pipeline_id 
        dest = config.MidiFiles.preprocessed_csv_files

        for item in os.listdir(dest):
            item_path = os.path.join(dest, item)
            os.remove(item_path)

        for item in os.listdir(files_path):
            s = os.path.join(files_path, item)
            d = os.path.join(dest, item)
            shutil.copy2(s, d)

    def run_pipeline(self, pick_up_from=None):
        pipeline_items = {
            "merge_midi_tracks": self.merge_midi_tracks,
            "convert_midis_to_csv": self.convert_midis_to_csv,
            "remove_meta_data": self.remove_meta_data,
            "preprocess_notes": self.preprocess_notes,
            "scale_timings": self.scale_timings,
            "calculate_note_durations": self.calculate_note_durations,
            "calculate_delta_times": self.calculate_delta_times,
            "finalize_preprocess": self.finalize_preprocess,
        }

        try_to_load = True
        index = 0
        func_id = None
        for name, func in pipeline_items.items():
            if pick_up_from == str(index) or pick_up_from == name:
                try_to_load = False

            index += 1
            
            func_id = func(try_to_load=try_to_load, last_pipeline_id=func_id)
        
        self.turn_in(func_id)
        self.save_progress()

def main(pick_up_from=None):
    preprocess = Preprocess()
    preprocess.run_pipeline(pick_up_from=pick_up_from)

if __name__ == "__main__":
    main()