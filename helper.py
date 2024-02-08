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

# Config Variables
HEADLESS_MODE = True

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

def set_logger(title: str = ""):
    """Logger config"""
    if title != "":
        title += "_"
        
    logging.basicConfig(
        filename=f"Logs/{title}{get_formatted_time()}.log",
        encoding="utf-8",
        format="%(asctime)s - %(levelname)s - %(thread)d -  %(funcName)s - %(message)s")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
