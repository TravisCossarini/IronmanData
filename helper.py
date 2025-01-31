"""Helper functions for scraping"""
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from pathlib import Path
import requests
import sys

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

def init_web_driver(link: str = "https://www.google.com/", headless: bool = HEADLESS_MODE):
    """Initializes a web driver for a given URL"""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    start_time = time.time()
    driver = webdriver.Chrome(options=options)
    driver.get(link)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    logging.info(f"Initializing Web Driver - waited {time.time() - start_time:.2f} for link {link}")
    return driver

def driver_get_new_page(driver: webdriver, link: str) -> webdriver:
    """Gets a new page for webdriver"""
    start_time = time.time()
    driver.get(link)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    logging.info(f"Getting new page - waited {time.time() - start_time:.2f} for link {link}")
    return driver

def get_page_source(link: str):
    """Returns the source for a given link"""
    driver = init_web_driver(link)
    source = driver.page_source
    driver.quit()
    return BeautifulSoup(source, "html.parser")

def get_formatted_time():
    """Returns formatted time for logging purposes"""
    current_time = datetime.now()
    formatted_time = current_time.strftime('%m_%d_%Y_%H_%M')
    return formatted_time

def make_request(url, method='GET', headers=None, data=None, params=None):
   response = requests.request(
       method=method,
       url=url,
       headers=headers,
       json=data,
       params=params
   )
   return response

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
