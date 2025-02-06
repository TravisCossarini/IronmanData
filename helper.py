"""Helper functions for scraping"""
import logging
from datetime import datetime
from pathlib import Path
import requests

# Config Variables
HEADLESS_MODE = False
IRONMAN_BASE_LINK = "https://www.ironman.com"
IRONMAN_RACES_LINK = f"{IRONMAN_BASE_LINK}/races"
IRONMAN_REQUEST_HEADER = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'en-US,en;q=0.9',
    'cache-control': 'max-age=0',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate', 
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
}


def make_request(url, method='GET', headers=None, data=None, params=None):
   """Makes request to endpoint and returns result"""
   response = requests.request(
       method=method,
       url=url,
       headers=headers,
       json=data,
       params=params
   )
   return response

def get_formatted_time():
    """Returns formatted time for logging purposes"""
    current_time = datetime.now()
    formatted_time = current_time.strftime('%m_%d_%Y_%H_%M')
    return formatted_time

def set_logger(title: str = "", output_file: bool = True, output_console: bool = True):
    """Logger config"""
    if title:
        title = f"_{title}"
        
    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(thread)d - %(funcName)s - %(message)s")

    # File handler
    if output_file:
        file_handler = logging.FileHandler(f"{Path.home()}/Code/IronmanData/Logs/{get_formatted_time()}{title}.log", encoding="utf-8")
        file_handler.setFormatter(formatter)

    # Console handler 
    if output_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

    # Setup logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if output_file:
        logger.addHandler(file_handler)
    if output_console:
        logger.addHandler(console_handler)
