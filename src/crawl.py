import requests
from bs4 import BeautifulSoup 
import re, config, tqdm, random, pandas as pd, os, time

def generate_random_string(length=16):
    chars = [chr(i) for i in range(97,123)]
    chars = ''.join(chars)
    chars += chars.upper()
    numbers = [str(i) for i in range(0,10)]
    numbers = ''.join(numbers)

    chars += numbers

    random_string = [random.choice(chars) for i in range(length)]
    
    return ''.join(random_string)

def extract_composers_urls():
    composers = requests.get(config.Crawl.base_url + config.Crawl.composers_url)
    soup = BeautifulSoup(composers.text, "html.parser")

    blockquote = soup.find_all(name='blockquote')
    blockquote = blockquote[1]

    lies = blockquote.find_all(name='a')
    composers_dict = {}
    for l in lies:
        if l.get('href') and '#' not in l.get('href'):
            composer_name = l.text[:-1].strip()
            link = l.get('href')
            composers_dict[composer_name] = link

    return composers_dict

def read_db(path=config.MidiFiles.database):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        headers = ["Composer", "Name", "FileName", "Url"]

        df = pd.DataFrame(columns=headers)
        df.to_csv(path, index=False)

    db = pd.read_csv(path)
    return db

def download_composers_midi(composers_dict, no_redownload=True):
    db = read_db()

    try:
        for composer_name, link in composers_dict.items():
            print(f"Download {composer_name} Files")

            page = requests.get(config.Crawl.base_url + link)

            page_soup = BeautifulSoup(page.text, "html.parser")

            pattern = r'^https://www\.midiworld\.com/.+\.mid$'
            pattern = re.compile(pattern)

            p = page_soup.find_all('a', href=pattern)

            for i in tqdm.tqdm(p, desc="Downloading MIDI files", unit="file"):
                music_name = i.text.strip().replace(' ', '_') 
                
                filename = [composer_name, music_name, generate_random_string(5)]
                filename = '_'.join(filename)
                filename = re.sub(r'[\/\\:*?"<>|\n\r\t]', '_', filename)
                filename += '.mid'
                url = i.get("href")
                
                # Check if we already have downloaded the file
                if no_redownload and url in db['Url'].values:
                    continue

                response = requests.get(url, stream=True)
        
                if response.status_code == 200:
                    with open(config.MidiFiles.raw_midi_files + '/' + filename, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                
                    row = {
                        "Composer": composer_name,
                        "Name": music_name,
                        "FileName": filename, 
                        "Url": url
                    }

                    db = pd.concat([db, pd.DataFrame([row])], ignore_index=True)
                
            db.to_csv(config.MidiFiles.database, index=False)
        
    except KeyboardInterrupt:
        db.to_csv(config.MidiFiles.database, index=False)
        print("Saved the progress!")

    except Exception as e:
        print(e)
        db.to_csv(config.MidiFiles.database, index=False)
        print("Saved the progress!")


if __name__ == "__main__":
    composers = extract_composers_urls()
    download_composers_midi(composers)