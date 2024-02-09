"""Gets the race data from all competitor labs urls and stores it as html files"""
import logging
import time
import os
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, TimeoutException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
import helper

# CONFIG VALUES
IRONMAN_BASE_LINK = "https://www.ironman.com"
IRONMAN_RACES_LINK = f"{IRONMAN_BASE_LINK}/races"
COMPETITOR_LAB_LINK = "https://labs.competitor.com/result/subevent/"
COMPETITOR_LAB_LINK_SUFFIX= "?filter=%7B%7D&order=ASC&perPage=50&sort=FinishRankOverall&page="
NUM_THREADS = 4
RETRY_COUNT = 3

def get_clab_data(clab_data_id: str):
    """Gets the data from all pages for a given clab event"""
    data_url_first_page = f"{COMPETITOR_LAB_LINK}{clab_data_id}{COMPETITOR_LAB_LINK_SUFFIX}1"
    driver = helper.init_web_driver(data_url_first_page)
    time.sleep(2)
    try:
        num_pages = int(driver.find_elements(By.XPATH, "//ul[contains(@class, 'MuiPagination-ul')]/li/button")[-2].text)
    except IndexError:
        # If there is only one page, handle error
        num_pages = 1
    logging.info(f"Extracing data for {clab_data_id} with {num_pages} pages")

    data_page_urls = [f"{COMPETITOR_LAB_LINK}{clab_data_id}{COMPETITOR_LAB_LINK_SUFFIX}{page_num}" for page_num in range(1, num_pages+1)]

    competitor_data_list = []
    for url in data_page_urls:
        competitor_data_list += clabs_page_data_extraction_handler(driver, url)

    save_str_list_to_file(clab_data_id, competitor_data_list)
    driver.quit()

def clabs_page_data_extraction_handler(driver: webdriver, data_url: str) -> list:
    """Function to handle extraction failures and facilitate retries for clab data"""
    current_page = data_url.split("=")[-1]
    clab_data_id = data_url[len(COMPETITOR_LAB_LINK): len(COMPETITOR_LAB_LINK)+36]
    logging.info(f"Extracting data for page {current_page}")
    driver = helper.driver_get_new_page(driver, data_url)
    error_count = 0
    complete_flag = False

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "tr"))
        )
    except TimeoutException:
        logging.error(f"Data page {current_page}, caused a timeout when waiting for data to load. Skipping race and page")
        return []

    while not complete_flag:
        try:
            page_values = clabs_extract_data_from_page(driver, current_page, clab_data_id)
            complete_flag = True
            return page_values
        except (StaleElementReferenceException, NoSuchElementException, ElementClickInterceptedException) as error:
            if error_count == RETRY_COUNT:
                logging.error(f"Retried page {data_url} {error_count} times, raising error: {error}")
                raise error
            
            logging.error(f"Retrying page {current_page}, retry count {error_count}: {error}")
            # Retry entire page
            driver.refresh()
            time.sleep(5)
            error_count += 1

def clabs_extract_data_from_page(driver: webdriver, current_page: int, race_data_id: str) -> list:
    """Extracts all data from a clab given page"""
    competitor_html_list = []
    start_time = time.time()

    table_rows = driver.find_elements(By.XPATH, "//tbody/tr")

    for idx, table_row in enumerate(table_rows):
        table_row.click()
        # Wait until data has loaded fully
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "swimDetails"))
                and EC.presence_of_element_located((By.ID, "bikeDetails"))
                and EC.presence_of_element_located((By.ID, "runDetails"))
                and EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'text') and contains(@class, 'countryFlag')]/img"))
            )
        except TimeoutException:
            logging.warning(f"Found row with no country on row {idx+1} on page {current_page}, timed out")

        expanded_table_row = driver.find_element(By.CLASS_NAME, "RaDatagrid-expandedPanel")
        row_html = table_row.get_attribute("outerHTML")
        data_html = expanded_table_row.get_attribute("outerHTML")

        # Click the row again to close
        table_row.click()
        WebDriverWait(driver, 5).until_not(
            EC.presence_of_element_located((By.ID, "swimDetails"))
        )

        # Add div for easier parsing
        total_html_row = f"<div class='extraction_dummy'>{row_html}{data_html}</div>"
        competitor_html_list.append(total_html_row)

    logging.info(f"Total execution time for race {race_data_id} and page {current_page} is {time.time() - start_time:.2f}")
    return competitor_html_list

def save_str_list_to_file(race_id: str, list_of_str: list):
    """
    Saves a list of strings to a text file
    """
    with open(f"Race Data HTML/{race_id}.html", "w", encoding="utf-8") as file:
        file.write("\n".join(list_of_str))

def main():
    """Main function for module"""
    helper.set_logger("clab_HTML_extraction")
    logging.info("Beginning extraction of competitor labs data")

    clab_data = pd.read_csv("Competitor Labs URLs.csv")
    existing_files = [file[:-5] for file in os.listdir(r"./Race Data HTML") if file.endswith(".html")]
    # Can also add one to check for csv

    for _, row in clab_data.iterrows():
        clab_id = row["Competitor Labs ID"]

        if clab_id not in existing_files:
            logging.info(f"Beginning {row['Race Id']} for year {row['Year']} and id {clab_id}")
            start_time_main = time.time()
            get_clab_data(clab_id)
            logging.info(f"Total extraction time for race {clab_id} is {time.time() - start_time_main:.2f}")

    return

if __name__ == "__main__":
    main()
