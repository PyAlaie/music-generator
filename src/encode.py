import config, os, tqdm, random, inspect, pickle, shutil

class Encode:
    def __init__(self, try_to_load_progress=True):
        self.preprocessed_csv_path = config.MidiFiles.preprocessed_csv_files
        self.try_to_load_progress = try_to_load_progress

        if try_to_load_progress and self.load_progress():
            pass
        else:
            self.preprocess_id = f"{self.__class__.__name__}_{self.generate_random_string(6)}"
            self.temp_space = config.MidiFiles.temp_space + '/' + self.preprocess_id
            self.progress = {}

    def generate_random_string(self, length=16):
        chars = [chr(i) for i in range(97,123)]
        chars = ''.join(chars)
        chars += chars.upper()

        random_string = [random.choice(chars) for i in range(length)]
        
        return ''.join(random_string)

    def extract_tags(self):
        files = os.listdir(self.preprocessed_csv_path)

        tags = []
        for file in tqdm.tqdm(files, desc="Extarcting tags"):
            with open(self.preprocessed_csv_path + '/' + file, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.split(',')

                if line[1] not in tags:
                    tags.append(line[1])
        
        return tags

    def load_progress(self):
        return False

if __name__ == "__main__":
    encode = Encode()

    print(encode.extract_tags())