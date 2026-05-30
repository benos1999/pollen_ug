import os
import csv
import json

import requests
requests.packages.urllib3.disable_warnings()
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib import robotparser

##################################################################################################
##################################################################################################

# Template functions for web scraping, covering session setup, robots.txt checking, fetching with retries, and parsing. Reused, not original.


def make_session(user_agent: str = "paldat-scraper/1.0 (+https://example.org)",
                 retries: int = 3, backoff: float = 0.3, timeout: int = 10) -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": user_agent})
    retry = Retry(total=retries, backoff_factor=backoff,
                  status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET", "POST"))
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    s.request_timeout = timeout
    return s


def allowed_by_robots(base_url: str, user_agent: str, path: str, logger) -> bool:
    """Check if path is allowed by robots.txt. Logs warning and returns False if blocked."""
    rp = robotparser.RobotFileParser()
    rp.set_url(base_url.rstrip("/") + "/robots.txt")
    try:
        rp.read()
        allowed = rp.can_fetch(user_agent, path)
        if not allowed:
            logger.warning('Blocked by robots.txt; aborting')
        return allowed
    except Exception:
        # If robots cannot be fetched, default to being conservative elsewhere
        logger.debug("robots.txt could not be read; proceeding with caution")
        return True


def fetch(session: requests.Session, url: str) -> str:
    resp = session.get(url, timeout=getattr(session, "request_timeout", 10), verify=False)
    resp.raise_for_status()
    return resp.text


def save_json(records, path: str, outdir: str = 'output'):
    os.makedirs(outdir, exist_ok=True)
    full_path = os.path.join(outdir, path)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def save_csv(records, path: str, outdir: str = 'output'):
    os.makedirs(outdir, exist_ok=True)
    full_path = os.path.join(outdir, path)
    # flatten keys and write one row per species
    fieldnames = set()
    for v in records.values():
        fieldnames.update(v.keys())
    fieldnames = sorted(fieldnames)
    with open(full_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for v in records.values():
            w.writerow({k: v.get(k, '') for k in fieldnames})

#################################################################################################
#################################################################################################