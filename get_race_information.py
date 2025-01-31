"""Process for getting all race id's from the Ironman website"""
import logging
import time
import concurrent.futures
import pandas as pd
import helper
import re
from bs4 import BeautifulSoup

# CONFIG VALUES
NUM_THREADS = 1

def get_race_ids():
    """Gets all race ids from the Ironman website"""
    logging.info("Getting race ids")
    race_ids = set()

    # Find all links to races
    regex = r'https://www\.ironman\.com/races/[^"]*'
    # Range is just a limited while loop, will break once no more data returned
    for page_num in range(0, 100):
        start_time = time.time()
        response = helper.make_request(url=f"{helper.IRONMAN_RACES_LINK}?page={page_num}", headers=helper.IRONMAN_REQUEST_HEADER)
        response_body = response.text
        matches = re.findall(regex, response_body)
        if(len(matches) < 1):
            break
        race_ids.update(matches)
        logging.info(f"Completed page {page_num} with {len(matches)} races in {round(time.time() - start_time, 2)} seconds")

    # Cut off URL from ID
    return [url.split("/")[-1] for url in race_ids]

def get_clab_event_id(race_id: str):
    """Gets the competitor lab ID for a given race"""
    logging.info(f"Getting competitor lab id for {race_id}")
    results_response = helper.make_request(url=f"{helper.IRONMAN_RACES_LINK}/{race_id}/results", headers=helper.IRONMAN_REQUEST_HEADER)
    results_html = BeautifulSoup(results_response.text, "html.parser")
    competitor_lab_id = results_html.find("iframe").get("src").split("/")[-1]
    return competitor_lab_id

def get_race_info(race_id: str):
    """Gets all race information for a given race id"""
    logging.info(f"Getting race info for {race_id}")
    race_link = f"{helper.IRONMAN_RACES_LINK}/{race_id}"
    race_html = helper.make_request(url=race_link, headers=helper.IRONMAN_REQUEST_HEADER)
    race_html = BeautifulSoup(race_html.text, "html.parser")

    try:
        race_object = {
            "Race Id": race_id,
            "Title": race_html.find("h1").text.strip(),
            "Swim Type": race_html.find("div", string="Swim").find_next_sibling().findChildren("span")[0].text,
            "Bike Type": race_html.find("div", string="Bike").find_next_sibling().findChildren("span")[0].text,
            "Run Type": race_html.find("div", string="Run").find_next_sibling().findChildren("span")[0].text,
            "High Air Temp": race_html.find("div", string="High Air Temp").find_next_sibling().findChildren("span")[0].text,
            "Low Air Temp": race_html.find("div", string="Low Air Temp").find_next_sibling().findChildren("span")[0].text,
            "Avg Water Temp": race_html.find("div", string="Avg. Water Temp").find_next_sibling().findChildren("span")[0].text,
            "Location": race_html.find("div", {"class", "country-flag-formatter"}).findChildren("span")[0].text,
            "Logo Image URL": f'{helper.IRONMAN_BASE_LINK}/{race_html.find("div", {"class", "race-logo"}).findChild("img").get("src")}',
            "Flag Image URL": f'{helper.IRONMAN_BASE_LINK}/{race_html.find("div", {"class", "country-flag-formatter"}).findChild("img").get("src")}',
            "Competitor Lab Id": get_clab_event_id(race_id)
        }
    except AttributeError as e:
        race_object = {
            "Race Id": race_id,
            "Title": "",
            "Swim Type": "",
            "Bike Type": "",
            "Run Type": "",
            "High Air Temp": "",
            "Low Air Temp": "",
            "Avg Water Temp": "",
            "Location": "",
            "Logo Image URL": "",
            "Flag Image URL": ""
        }
    return race_object

def get_all_races_info():
    """Gets the information for all races listed on the Ironman website"""
    helper.set_logger()
    logging.info("Beginning extraction of race information")
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        races = list(executor.map(get_race_info, get_race_ids()))

    pd.DataFrame(races).to_csv("Race Information.csv", index=False)

if __name__ == "__main__":
    start_time = time.time()
    get_all_races_info()
    logging.info(f"Total execution time {time.time() - start_time:.2f}")
