"""paldat_scraper.py

A modular, professional-style scraper for paldat.org converted from the notebook.

Features:
- requests.Session with retries and timeouts
- robots.txt check, polite delays with jitter
- separate fetch / parse / save functions
- CLI with arguments for output and whether to download images
"""
import argparse
import logging
import os
import random
import time

import requests
requests.packages.urllib3.disable_warnings()
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

import scrape_utils


logger = logging.getLogger(__name__)


# @dataclass
# class SpeciesRecord:
#     Species: str
#     Genus: str
#     Family: Optional[str] = None
#     Order: Optional[str] = None
#     Class: Optional[str] = None
#     Phylum: Optional[str] = None
#     imgs: List[str] = None




def scrape_paldat_values(soup: BeautifulSoup):
    keys = [item.get_text().replace(':', '').replace('\xa0', ' ').strip()
            for item in soup.find_all('span', class_='diag-label')]
    values = [item.get_text().strip() for item in soup.find_all('span', class_='diag-value')]
    value_dict = {k: v for k, v in zip(keys, values)}

    # Species and Genus
    species_tag = soup.find(class_='species')
    genus_tag = soup.find(class_='genus')
    value_dict['Species'] = species_tag.get_text(strip=True) if species_tag else ''
    value_dict['Genus'] = genus_tag.get_text(strip=True) if genus_tag else ''

    # Taxonomy parsing (best-effort)
    try:
        tax_text = soup.find('p').get_text()
        tax_text = tax_text.replace('Taxonomy:', '').replace(',', '')
        parts = [p.strip() for p in tax_text.splitlines() if p.strip()]
        # heuristic mapping from the notebook: last items correspond to higher levels
        taxonomy_levels = ['Family', 'Order', 'Class', 'Phylum']
        # reverse parts and pick values
        rev = [p for p in parts[::-1] if p]
        for i, level in enumerate(taxonomy_levels):
            if i < len(rev):
                value_dict[level] = rev[i]
    except Exception:
        logger.debug('taxonomy parsing failed', exc_info=True)

    return value_dict


def parse_genus_links(html: str):
    soup = BeautifulSoup(html, features = 'lxml')
    return ['https://www.paldat.org' + a.get('href') for a in soup.find_all('a', class_='genus')]


def parse_species_links(html: str):
    soup = BeautifulSoup(html, features = 'lxml')
    return ['https://www.paldat.org' + a.get('href') for a in soup.find_all('a', class_='species')]


def download_images(session: requests.Session, soup: BeautifulSoup, outdir: str, id_counter: int,
                    species_name: str):
    os.makedirs(outdir, exist_ok=True)
    saved = []
    for link in soup.find_all('a', id='pic_0'):
        href = link.get('href')
        if not href:
            continue
        full = 'https://www.paldat.org' + href
        try:
            img_data = session.get(full, timeout=getattr(session, 'request_timeout', 10), verify=False).content
            title = link.get('data-title') or species_name
            filename = f"{title}_{id_counter}.jpg"
            path = os.path.join(outdir, filename)
            with open(path, 'wb') as f:
                f.write(img_data)
            saved.append(filename)
            id_counter += 1
        except Exception:
            logger.exception('failed to download image %s', full)
    return saved, id_counter



def run(out_json: str = 'paldat_out.json', out_csv: str = 'paldat_out.csv', download_images_flag: bool = True,
        images_dir: str = 'images', sleep_min: float = 1.0, sleep_max: float = 3.0):
    session = scrape_utils.make_session()
    base = 'https://www.paldat.org'
    # check robots for main search
    if not scrape_utils.allowed_by_robots(base, session.headers.get('User-Agent', ''), '/search'):
        logger.warning('Blocked by robots.txt; aborting')
        return

    # gather genus links
    links = []
    for letter in [chr(i) for i in range(ord('A'), ord('Z') + 1)]:
        url = f'{base}/search/{letter}'
        try:
            html = scrape_utils.fetch(session, url)
            links.extend(parse_genus_links(html))
            time.sleep(random.uniform(sleep_min, sleep_max))
        except Exception:
            logger.exception('failed to fetch genus page %s', url)

    # gather species links
    species_links = []
    for link in links:
        try:
            html = scrape_utils.fetch(session, link)
            species_links.extend(parse_species_links(html))
            time.sleep(random.uniform(sleep_min, sleep_max))
        except Exception:
            logger.exception('failed to fetch genus detail %s', link)

    # scrape species pages
    values_dict = {}
    id_counter = 0
    for link in species_links:
        try:
            html = scrape_utils.fetch(session, link)
            soup = BeautifulSoup(html, features = 'lxml')
            values = scrape_paldat_values(soup)
            name = values.get('Species') or values.get('Genus') or link
            values_dict[name] = values
            values_dict[name].setdefault('imgs', [])
            if download_images_flag:
                saved, id_counter = download_images(session, soup, images_dir, id_counter, name)
                values_dict[name]['imgs'].extend(saved)
            # polite delay
            time.sleep(random.uniform(sleep_min, sleep_max))
        except Exception:
            logger.exception('failed to scrape species %s', link)

    # persist
    scrape_utils.save_json(values_dict, out_json)
    scrape_utils.save_csv(values_dict, out_csv)
    logger.info('finished: %d species saved', len(values_dict))


def cli_main():
    p = argparse.ArgumentParser(description='PALDat scraper')
    p.add_argument('--no-images', action='store_true', help='Do not download images')
    p.add_argument('--out-json', default='paldat_out.json')
    p.add_argument('--out-csv', default='paldat_out.csv')
    p.add_argument('--images-dir', default='images')
    p.add_argument('--min-sleep', type=float, default=1.0)
    p.add_argument('--max-sleep', type=float, default=3.0)
    args = p.parse_args()
    logging.basicConfig(filename = f'{__name__}.log',level=logging.INFO)
    run(out_json=args.out_json, out_csv=args.out_csv,
        download_images_flag=not args.no_images, images_dir=args.images_dir,
        sleep_min=args.min_sleep, sleep_max=args.max_sleep)


if __name__ == '__main__':
    cli_main()
