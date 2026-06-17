"""GPP_scraper.py

A modular scraper for the Global Pollen Project converted from the notebook.

Features:
- requests.Session with retries and timeouts
- robots.txt check, polite delays with jitter
- separate fetch / parse / save functions
- CLI with arguments for output and whether to download images
"""

import argparse
import json
import logging
import os
import random
import time

import requests
requests.packages.urllib3.disable_warnings()
from bs4 import BeautifulSoup

import scrape_utils

logger = logging.getLogger(__name__)

def download_images(link: str, outdir: str, id_counter: int, out_json: str = os.path.join("output", "gpp_out.json")):
    os.makedirs(outdir, exist_ok=True)
    
    if os.path.exists(out_json):
        with open(out_json, 'r') as f:
            values_dict = json.load(f) 
            logger.info('loaded existing values_dict with %d species', len(values_dict))
    else:
        values_dict = {}

    session = scrape_utils.make_session()
    html = requests.get(f'{link}', timeout=getattr(session, 'request_timeout', 10), verify=False)
    logger.info('retrieved %s', link)
    
    family_name = html.json()['Family']

    for slide in html.json()['Slides']:
        species_name = slide.get('LatinName', 'Unknown_Species')
        saved = []
        url = f"https://globalpollenproject.org/Reference/{slide['ColId']}/{slide['SlideId'].replace(' ', '%20')}"
        img = requests.get(url)
        soup = BeautifulSoup(img.content, 'html.parser')
        elements = soup.select('div .slide-gallery-item.col-md-3')
        logger.info('retrieved %s and made the soup', url)
        
        for element in elements:
                try:    
                    img_url = element.get('data-frames', []).split(',')[0].replace('[', '').replace(']', '').replace('"', '').strip()                    
                    img_data = session.get(img_url, timeout=getattr(session, 'request_timeout', 10), verify=False).content
                    filename = f"{species_name}_{id_counter}.jpg"                
                    path = os.path.join('GPP_images', filename)
                    with open(path, 'wb') as f:
                        f.write(img_data)
                    saved.append(filename)
                    id_counter += 1
                except Exception:
                    logger.exception('failed to download images for species %s', species_name)
        values_dict[species_name] = {'images': saved, 'family': family_name}
        time.sleep(random.uniform(1.0, 3.0))
        logger.info('finished: %d images saved', len(saved))
        logger.info('finished: %d species saved', len(values_dict))
    if os.path.exists(out_json):
        logger.info('json path exists %s', values_dict)
        with open(out_json, 'w') as f:
            json.dump(values_dict, f, indent=2)
    else:
        logger.info('writing new json with %s species', values_dict)
        with open(out_json, 'w') as f:
            json.dump(values_dict, f, indent=2)
    
    return id_counter


def run(out_json: str = os.path.join("output", "gpp_out.json"), out_csv: str = os.path.join("output", "gpp_out.csv"), download_images_flag: bool = True,
        images_dir: str = 'GPP_images', sleep_min: float = 1.0, sleep_max: float = 3.0):
    session = scrape_utils.make_session()
    # base = 'https://api.globalpollenproject.org'
    # check robots for main search
    # if not scrape_utils.allowed_by_robots(base, session.headers.get('User-Agent', ''), '/search', logger):
    #     return
    
    genus_links = []

    for page in range(1, 6):
        try:
            genus_pages = scrape_utils.fetch(session,f'https://globalpollenproject.org/Taxon?rank=Family&lex=&page={page}')
            soup = BeautifulSoup(genus_pages, features='lxml')
            genus_links.extend([f'https://api.globalpollenproject.org/api/v1{url.get("href")}' for url in soup.select('.taxon-name')])
            logger.info('finished page %d, total links so far: %d', page, len(genus_links))
        except Exception:
            logger.exception('failed to fetch family page %d', page)
        time.sleep(random.uniform(sleep_min, sleep_max))
    # scrape species pages
    id_counter = 0
    for link in genus_links:
        try:
            if download_images_flag:
                id_counter = download_images(link, images_dir, id_counter)    
            # polite delay
            time.sleep(random.uniform(sleep_min, sleep_max))
        except Exception:
            logger.exception('failed to scrape species %s', link)    
    
    scrape_utils.save_csv(json.load(open(out_json, 'r')), out_csv)

     
     

def cli_main():
    p = argparse.ArgumentParser(description='GPP scraper')
    p.add_argument('--no-images', action='store_true', help='Do not download images')
    p.add_argument('--out-json', default=os.path.join("output", "gpp_out.json"))
    p.add_argument('--out-csv', default=os.path.join("output", "gpp_out.csv"))
    p.add_argument('--images-dir', default='GPP_images')
    p.add_argument('--min-sleep', type=float, default=1.0)
    p.add_argument('--max-sleep', type=float, default=3.0)
    args = p.parse_args()
    logging.basicConfig(filename = f'{__name__}.log',level=logging.INFO)
    run(out_json=args.out_json, out_csv=args.out_csv,
        download_images_flag=not args.no_images, images_dir=args.images_dir,
        sleep_min=args.min_sleep, sleep_max=args.max_sleep)


if __name__ == '__main__':
    cli_main()
