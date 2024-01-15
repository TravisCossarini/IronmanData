'''Gets the race data from all competitor labs urls'''
import logging
import time
import os
import concurrent.futures
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
import helper

# CONFIG VALUES
IRONMAN_BASE_LINK = 'https://www.ironman.com'
IRONMAN_RACES_LINK = f'{IRONMAN_BASE_LINK}/races'
COMPETITOR_LAB_LINK = 'https://labs.competitor.com/result/subevent/'
COMPETITOR_LAB_LINK_SUFFIX= '?filter=%7B%7D&order=ASC&perPage=50&sort=FinishRankOverall&page='
NUM_THREADS = 4
RETRY_COUNT = 3

def get_clab_data(clab_data_id: str) -> dict:
    '''Gets the data from all pages for a given clab event, handles threading'''
    data_url_first_page = f'{COMPETITOR_LAB_LINK}{clab_data_id}{COMPETITOR_LAB_LINK_SUFFIX}1'
    driver = helper.init_web_driver(data_url_first_page)
    time.sleep(2)
    
    num_pages = int(driver.find_elements(By.XPATH, '//ul[contains(@class, "MuiPagination-ul")]/li/button')[-2].text)
    driver.quit()
    logging.info(f'Extracing data for {clab_data_id} with {num_pages} pages')

    data_page_urls = [f'{COMPETITOR_LAB_LINK}{clab_data_id}{COMPETITOR_LAB_LINK_SUFFIX}{page_num}' for page_num in range(1, num_pages+1)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        pages_data_list = list(executor.map(clabs_data_extraction_handler, data_page_urls))

    competitor_data_list = []
    for page_data in pages_data_list:
        competitor_data_list += page_data

    return pd.DataFrame(competitor_data_list)

def clabs_data_extraction_handler(data_url: str):
    '''Function to handle extraction failures and facilitate retries for clab data'''
    current_page = data_url.split('=')[-1]
    clab_data_id = data_url[len(COMPETITOR_LAB_LINK): len(COMPETITOR_LAB_LINK)+36]
    logging.info(f'Extracting data for page {current_page}')
    driver = helper.init_web_driver(data_url)
    error_count = 0
    complete_flag = False

    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.TAG_NAME, 'tr'))
    )

    # Retry 
    while not complete_flag:
        try:
            page_values = clabs_extract_data_from_page(driver, current_page, clab_data_id)
            complete_flag = True
            driver.quit()
            return page_values
        except (StaleElementReferenceException, NoSuchElementException) as error:
            logging.error(f'Retrying page {current_page}, retry count : {error}')
            time.sleep(5)
            error_count += 1
            if error_count == RETRY_COUNT:
                logging.error(f'Retried page {error_count} times, raising error')
                raise

def clabs_extract_data_from_page(driver: webdriver, current_page: int, race_data_id: str):
    '''Extracts all data from a clab given page'''
    DNF_DESIGNATIONS = ['DNS', 'DNF', 'DQ']
    competitor_data_list = []
    table_rows = driver.find_elements(By.XPATH, '//tbody/tr')

    for idx, table_row in enumerate(table_rows):
        logging.info(f'Extracting from row {idx+1} on page {current_page}')
        table_row.click()
        # Wait until country flag has loaded -> implies the rest of the data has loaded as well
        WebDriverWait(driver, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, '//div[contains(@class, "text") and contains(@class, "countryFlag")]/img'))
        )

        summary_rows = driver.find_elements(By.CLASS_NAME, 'detailsButton')
        for row in summary_rows:
            time.sleep(0.25)
            row.click()

        designation = driver.find_element(By.XPATH, '//p[text()="Designation"]/preceding-sibling::p').text
        dnf_flag = True if designation in DNF_DESIGNATIONS else False

        competitor_data = {
            'data_source_id': race_data_id,
            'Name': table_row.find_elements(By.TAG_NAME, 'span')[1].text,
            'Designation': designation,
            'Div Rank' : driver.find_element(By.XPATH, '//p[text()="Div Rank"]/preceding-sibling::p').text if not dnf_flag else '',
            'Gender Rank': driver.find_element(By.XPATH, '//p[text()="Gender Rank"]/preceding-sibling::p').text if not dnf_flag else '',
            'Overall Rank': driver.find_element(By.XPATH, '//p[text()="Overall Rank"]/preceding-sibling::p').text if not dnf_flag else '',
            'Bib': driver.find_elements(By.XPATH, '//div[contains(@class, "tableRow") and contains(@class, "tableFooter")]/div/div')[0].text,
            'Division': driver.find_elements(By.XPATH, '//div[contains(@class, "tableRow") and contains(@class, "tableFooter")]/div/div')[1].text,
            'Country': driver.find_element(By.XPATH, '//div[contains(@class, "text") and contains(@class, "countryFlag")]/img').get_attribute('alt'),
            'Points': driver.find_elements(By.XPATH, '//div[contains(@class, "tableRow") and contains(@class, "tableFooter")]/div/div')[3].text,
            'Swim Time': driver.find_elements(By.XPATH, '//div[contains(@id, "swimDetails")]/div/div/div/div')[4].text,
            'Swim Div Rank': driver.find_elements(By.XPATH, '//div[contains(@id, "swimDetails")]/div/div/div/div')[5].text,
            'Swim Gender Rank': driver.find_elements(By.XPATH, '//div[contains(@id, "swimDetails")]/div/div/div/div')[6].text,
            'Swim Overall Rank': driver.find_elements(By.XPATH, '//div[contains(@id, "swimDetails")]/div/div/div/div')[7].text,
            'Bike Time': driver.find_elements(By.XPATH, '//div[contains(@id, "bikeDetails")]/div/div/div/div')[4].text,
            'Bike Div Rank': driver.find_elements(By.XPATH, '//div[contains(@id, "bikeDetails")]/div/div/div/div')[5].text,
            'Bike Gender Rank': driver.find_elements(By.XPATH, '//div[contains(@id, "bikeDetails")]/div/div/div/div')[6].text,
            'Bike Overall Rank': driver.find_elements(By.XPATH, '//div[contains(@id, "bikeDetails")]/div/div/div/div')[7].text,
            'Run Time': driver.find_elements(By.XPATH, '//div[contains(@id, "runDetails")]/div/div/div/div')[4].text,
            'Run Div Rank': driver.find_elements(By.XPATH, '//div[contains(@id, "runDetails")]/div/div/div/div')[5].text,
            'Run Gender Rank': driver.find_elements(By.XPATH, '//div[contains(@id, "runDetails")]/div/div/div/div')[6].text,
            'Run Overall Rank': driver.find_elements(By.XPATH, '//div[contains(@id, "runDetails")]/div/div/div/div')[7].text,
            'Transition 1': driver.find_elements(By.XPATH, '//div[contains(@id, "transitions")]/div/div/div/div')[2].text,
            'Transition 2': driver.find_elements(By.XPATH, '//div[contains(@id, "transitions")]/div/div/div/div')[3].text,
            'Overall Time': driver.find_element(By.XPATH, '//div[contains(@class, "summaryRow") and contains(@class, "overallRow")]/p[contains(@class, "summaryTime")]').text
        }
        # Close the current row
        table_row.click()
        competitor_data_list.append(competitor_data)

    return competitor_data_list

def main():
    '''Main function for module'''
    helper.set_logger()
    
    clab_data = pd.read_csv('Competitor Labs URLs.csv')
    existing_files = [file[:-4] for file in os.listdir(r'./Race Data') if file.endswith('.csv')]

    for _, row in clab_data.iterrows():
        clab_id = row['Competitor Labs ID']
        logging.info(f'Beginning {row["Race Id"]} for year {row["Year"]} and id {clab_id}')

        if clab_id not in existing_files:
            get_clab_data(clab_id).to_csv(f'Race Data/{clab_id}.csv')

if __name__ == '__main__':
    start_time = time.time()
    main()
    logging.info(f'Total Execution time {time.time() - start_time:.2f}')
