'''Process for getting all race id's from the Ironman website'''
import logging
import time
import concurrent.futures
import pandas as pd
from selenium.webdriver.common.by import By
import helper

# CONFIG VALUES
IRONMAN_BASE_LINK = 'https://www.ironman.com'
IRONMAN_RACES_LINK = f'{IRONMAN_BASE_LINK}/races'
NUM_THREADS = 4

def get_race_ids():
    '''Gets all race ids from the Ironman website'''
    logging.info('Getting race ids')
    driver = helper.init_web_driver(IRONMAN_RACES_LINK)
    race_ids = []

    next_page_button_css = '.nextPageButton:not(.hidden)'
    next_page_button = driver.find_element(By.CSS_SELECTOR, next_page_button_css)
    page_count = 1

    # While there is a next page button visible
    while next_page_button:
        logging.info(f'Scraping page {page_count}')
        race_ids += [link.get_attribute('href').split('/')[-1] for link in driver.find_elements(By.LINK_TEXT, 'See Race Details')]

        # Check to see if this is the last page
        if 'hidden' in next_page_button.get_attribute('class'):
            logging.info(f'Found last page, ending execution')
            break
        else:
            driver.execute_script('arguments[0].click();', next_page_button)
            page_count += 1

    logging.info(f"Retrieved {len(race_ids)} race ids")
    driver.quit()
    return race_ids

def get_race_info(race_id: str):
    '''Gets all race information for a given race id'''
    logging.info(f'Getting race info for {race_id}')
    race_link = f'{IRONMAN_BASE_LINK}/{race_id}'
    race_html = helper.get_page_source(race_link)

    race_object = {
        'Race Id': race_id,
        'Title': race_html.find('h1').text,
        'Swim Type': race_html.find('div', class_='swim-type').text[5:-1],
        'Bike Type': race_html.find('div', class_='bike-type').text[5:-1],
        'Run Type': race_html.find('div', class_='run-type').text[4:-1],
        'Avg Air Temp': race_html.find('div', class_='airTemp').text.split('Temp')[-1][:-1],
        'Avg Water Temp': race_html.find('div', class_='waterTemp').text.split('Temp')[-1][:-1],
        'Airport': race_html.find('div', class_='airport').text[8:-1]
    }
    return race_object

def get_all_races_info():
    '''Gets the information for all races listed on the Ironman website'''
    helper.set_logger()
    logging.info('Beginning extraction of race information')
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        races = list(executor.map(get_race_info, get_race_ids()))

    pd.DataFrame(races).to_csv('Race Information.csv', index=False)

if __name__ == '__main__':
    start_time = time.time()
    get_all_races_info()
    logging.info(f'Total Execution time {time.time() - start_time:.2f}')
