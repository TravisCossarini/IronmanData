"""Gets all Competitor Lab data urls and their related information as well as some basic validation"""
import logging
import time
import concurrent.futures
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException, NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
import helper

# CONFIG VALUES
IRONMAN_BASE_LINK = "https://www.ironman.com"
IRONMAN_RACES_LINK = f"{IRONMAN_BASE_LINK}/races"
COMPETITOR_LAB_LINK = "https://labs.competitor.com/result/subevent/"
COMPETITOR_LAB_LINK_SUFFIX= "?filter=%7B%7D&order=ASC&perPage=50&sort=FinishRankOverall&page="
NUM_THREADS = 4
RACE_IDS_FILE = "Race Information.csv"

def get_competitor_labs_urls(race_id: str):
    """Gets all clab urls for a given race id by clicking through the tabs of the iframe node"""
    logging.info(f"Getting data page for race {race_id}")
    results_link = f"{IRONMAN_BASE_LINK}/{race_id}-results"

    driver = helper.init_web_driver(results_link)
    # Wait for cookies form to load
    time.sleep(5)
    try:
        driver.find_element(By.ID, "onetrust-reject-all-handler").click()
    except NoSuchElementException as error:
        logging.warning(f"No cookies found on {race_id} --- {error}")


    race_competitor_labs_urls = []
    current_year_url_ids = set()
    years = set()

    results_years_buttons = driver.find_elements(By.CSS_SELECTOR, ".tab-remote")
    # results_years_buttons = driver.find_elements(By.XPATH, "//span[text()='Results']/../../../following-sibling::div/div/ul/li/span/a")

    for result_year in results_years_buttons:
        try:
            result_year.click()
            time.sleep(10)
            iframes_list = driver.find_elements(By.XPATH, f"//iframe[contains(@src, '{COMPETITOR_LAB_LINK}')]")

            for iframe in iframes_list:
                iframe_url = iframe.get_attribute("src")
                current_year_url_ids.add(iframe_url.split("/")[-1])
                years.add(result_year.text if result_year.text != "" else "Blank")

            logging.info(f"Competitor labs ID retreived for {race_id} - {result_year.text}")
        except (ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException, NoSuchElementException) as error:
            logging.warning(f"Error element on {race_id} - {result_year.text} for year {result_year.text} --- {error}")

    race_object = {
        "id": race_id,
        "competitor_lab_ids": ", ".join(list(current_year_url_ids)),
        "years": ", ".join(list(years)) # Included for QA
    }
    race_competitor_labs_urls.append(race_object)

    driver.quit()
    return race_competitor_labs_urls

def get_all_race_data_urls(race_ids: list):
    """Gets all of the competitor lab urls for a given set of race ids"""
    race_dimension_info = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        result_urls = list(executor.map(get_competitor_labs_urls, race_ids))

    for urls in result_urls:
        race_dimension_info += urls

    return pd.DataFrame(race_dimension_info)

def fetch_competitor_labs_information(clab_id: str):
    """Gets the supporting information such as year for each competitor labs url"""
    results_link = f"{COMPETITOR_LAB_LINK}{clab_id}"
    driver = helper.init_web_driver(results_link)
    logging.info(f"Getting year from clabs for {results_link}")

    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.XPATH, "//*[@id='react-admin-title']/span/span/span"))
    )
    return driver.find_element(By.XPATH, "//*[@id='react-admin-title']/span/span/span").text.split(" ")[0]

def compare_race_data(df1: pd.DataFrame, df2: pd.DataFrame):
    """Compares the competitor lab urls gathered from a race"""
    # Ugly function, I know
    formatted_output_list = []
    for _, row1 in df1.iterrows():
        for _, row2 in df2.iterrows():
            if row1["id"] == row2["id"]:
                if row1["competitor_lab_ids"] != row2["competitor_lab_ids"] and row1["years"] != row2["years"]:
                    logging.warn(f"Race {IRONMAN_BASE_LINK}/{row1['id']}-results has no data or there was an error extracting the urls")
                else:
                    for clab_id in row1["competitor_lab_ids"].split(", "):
                        clabs_info = {
                            "Race Id": row1["id"],
                            "Competitor Labs ID": clab_id,
                            "Year": fetch_competitor_labs_information(clab_id)
                        }
                        formatted_output_list.append(clabs_info)
    
    return pd.DataFrame(formatted_output_list)

def main():
    """Main function for module"""
    helper.set_logger()
    logging.info("Beginning extraction of competitor labs urls")
    
    race_ids = pd.read_csv("Race Information.csv")["Race Id"].to_list()
    # Do it twice to make sure that we got them all. There is latency on the website which sometimes causes errors.
    clab_urls_1 = get_all_race_data_urls(race_ids)
    clab_urls_2 = get_all_race_data_urls(race_ids)

    try:
        final_data = compare_race_data(clab_urls_1, clab_urls_2)
        final_data.to_csv("Competitor Labs URLs.csv", index=False)
    except TimeoutException as error:
        logging.error(f"Error getting year for each URL: {error}")
        clab_urls_1.to_csv("clab_url_1.csv", index=False)
        clab_urls_2.to_csv("clab_url_2.csv", index=False)

if __name__ == "__main__":
    start_time = time.time()
    main()
    logging.info(f"Total Execution time {time.time() - start_time:.2f}")
