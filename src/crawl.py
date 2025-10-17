import asyncio
import pathlib
import re
import random
import os

import requests
from bs4 import BeautifulSoup 
from tqdm.asyncio import tqdm
import pandas as pd
import aiohttp
import config


STREAM_CHUNK_SIZE = config.Crawl.STREAM_CHUNK_SIZE


async def batch_download(info, callback=None, max_conn=32, progress=True, progress_settings={}):
    q = asyncio.Queue()
    callback_lock = asyncio.Lock()
    if progress:
        pg = tqdm(total=len(info), **progress_settings)

    # TODO: handle task cancellation.
    async def worker():
        while True:
            url, path, *args = await q.get()

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    with open(path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(STREAM_CHUNK_SIZE):
                            f.write(chunk)
                    if progress:
                        pg.update(1)
                    if callback:
                        async with callback_lock:
                            await callback(*args)
            q.task_done()
        
    tasks = [asyncio.create_task(worker()) for _ in range(max_conn)]
    for download_info in info:
        await q.put(download_info)
    await q.join()
    for t in tasks:
        t.cancel()
    

def generate_random_string(length=16):
    chars = [chr(i) for i in range(ord('a'), ord('z')+1)]
    chars = [chr(i) for i in range(ord('A'), ord('Z')+1)]
    chars.extend([str(i) for i in range(10)])
    return ''.join(random.choices(chars, k=length))


def extract_composers_urls():
    composers = requests.get(config.Crawl.base_url + config.Crawl.composers_url)
    soup = BeautifulSoup(composers.text, 'html.parser')

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


def extract_composer_tracks(composer_page_url):
    page = requests.get(composer_page_url)

    page_soup = BeautifulSoup(page.text, 'html.parser')

    pattern = r'^https://www\.midiworld\.com/.+\.mid$'
    pattern = re.compile(pattern)

    p = page_soup.find_all('a', href=pattern)

    tracks = []
    for i in p:
        track_name = i.text.strip().replace(' ', '_')
        url = i.get('href')
        tracks.append((track_name, url))

    return tracks


def read_db(path=config.MidiFiles.database):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        headers = ['Composer', 'Name', 'FileName', 'Url']

        df = pd.DataFrame(columns=headers)
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)

    db = pd.read_csv(path)
    return db


def download_composers_midi(composers_dict, no_redownload=True):
    db = read_db()
    pathlib.Path(config.MidiFiles.raw_midi_files).mkdir(parents=True, exist_ok=True)
   
    async def _download_callback(row):
        nonlocal db
        db = pd.concat([db, pd.DataFrame([row])], ignore_index=True)

    try:
        for composer_name, link in composers_dict.items():
            print(f'Download {composer_name} Files')

            download_info = []
            composer_tracks = extract_composer_tracks(config.Crawl.base_url + link)

            for track in composer_tracks:
                track_name, track_url = track

                filename = f'{composer_name}_{track_name}_{generate_random_string(5)}.mid'
                filename = re.sub(r'[\/\\:*?"<>|\n\r\t]', '_', filename)
                
                # Check if we already have downloaded the file
                if no_redownload and track_url in db['Url'].values:
                    continue

                row = {
                    'Composer': composer_name,
                    'Name': track_name,
                    'FileName': filename, 
                    'Url': track_url
                }

                download_info.append((track_url, config.MidiFiles.raw_midi_files / filename, row))

            asyncio.run(
                batch_download(
                    download_info,
                    _download_callback, 
                    progress_settings={'desc': 'Downloading MIDI Files'}
                )
            )
            db.to_csv(config.MidiFiles.database, index=False)
    finally:
        db.to_csv(config.MidiFiles.database, index=False)
        print('Saved the progress!')

def main():
    composers = extract_composers_urls()
    download_composers_midi(composers)

if __name__ == '__main__':
    main()