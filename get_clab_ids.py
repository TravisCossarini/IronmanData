"""Gets all Competitor Lab data ids and their related information as well as some basic validation"""
import logging
import time
import concurrent.futures
import pandas as pd
import helper
from bs4 import BeautifulSoup
import json

# CONFIG VALUES
COMPETITOR_LAB_EVENT_LINK = "https://labs-v2.competitor.com/results/event"
COMPETITOR_LAB_EVENT_LINK_OPEN = "https://labs-v2.competitor.com/results/event/odiv"
# COMPETITOR_LAB_EVENT_LINK_TRICLUB = "https://labs-v2.competitor.com/clubpoints/event"
NUM_THREADS = 4
RACE_IDS_FILE = "Race Information.csv"

def get_competitor_labs_urls(race_id: str, clab_event_id: str):
    """Gets all clab urls for a given race id"""
    start_time = time.time()
    logging.info(f"Getting subevents for {race_id} with clab id {clab_event_id}")
    race_clab_subevents = []

    for url in [COMPETITOR_LAB_EVENT_LINK, COMPETITOR_LAB_EVENT_LINK_OPEN]:
        subevent_response = helper.make_request(f"{url}/{clab_event_id}", headers=helper.IRONMAN_REQUEST_HEADER)
        subevent_html = BeautifulSoup(subevent_response.text, "html.parser")
        try:
            subevent_html = subevent_html.find("script", {'id': '__NEXT_DATA__'}).string
        except AttributeError as e:
            logging.error("ERRROR Likely blocked by IP address")
            raise e
        subevents = json.loads(subevent_html)
        if("err" not in subevents):
            subevents = subevents["props"]["pageProps"]["subevents"]
        else:
            logging.error(f"{race_id} failed with error {subevents['err']["name"]}: {subevents['err']["message"]} ")
            return race_clab_subevents

        for subevent in subevents:
            subevent_dict = {
                "Race Id": race_id,
                "Name": subevent["wtc_name"],
                "Event Date": subevent["wtc_eventdate_formatted"],
                "Subevent Id": subevent["wtc_eventid"]
            }
            race_clab_subevents.append(subevent_dict)
    logging.info(f"Got {len(race_clab_subevents)} subevents for race {race_id} {round(time.time() - start_time, 2)} seconds")
    return race_clab_subevents

def get_all_clab_subevents(race_data: pd.DataFrame):
    """Gets all of the competitor lab urls for a given set of race ids"""
    logging.info(f"Getting all subevents for {race_data.shape[0]} races")
    clab_subevents = []

    race_ids = race_data["Race Id"].to_list()
    clab_event_ids = race_data["Competitor Lab Id"].to_list()

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        result_subevents = list(executor.map(get_competitor_labs_urls, race_ids, clab_event_ids))

    for subevents in result_subevents:
        clab_subevents += subevents
    return pd.DataFrame(clab_subevents).drop_duplicates()

def main():
    """Main function for module"""
    helper.set_logger()
    logging.info("Beginning extraction of competitor labs urls")
    
    race_data = pd.read_csv("Race Information.csv")

    clab_subevents = get_all_clab_subevents(race_data)
    clab_subevents.to_csv("Competitor Labs Subevents.csv", index=False)

if __name__ == "__main__":
    start_time = time.time()
    main()
    logging.info(f"Total Execution time {time.time() - start_time:.2f}")
