"""Gets the race data from all competitor labs urls and stores it as html files"""
import logging
import time
import pandas as pd
import helper
import json
import concurrent.futures

# CONFIG VALUES
COMPETITOR_LAB_API = "https://api.competitor.com/public/result/subevent"
PARTICIPANTS_PER_PAGE = 200
COMPETITOR_LAB_API_SUFFIX= f"?%24limit={PARTICIPANTS_PER_PAGE}&%24skip="
SUBSCRIPTION_KEY = "73f0c80357b249f189c34dc78ac7b118"
NUM_THREADS = 6

def get_clab_data(clab_data_id: str):
    """Gets the data from all pages for a given clab subevent
    
    returns: List of dictionaries, one dict per participant
    """
    # Add subscription key to header
    helper.IRONMAN_REQUEST_HEADER.update({"wtc_priv_key": SUBSCRIPTION_KEY})
    
    # Make first request to determine total number of participants
    subevent_data = helper.make_request(f"{COMPETITOR_LAB_API}/{clab_data_id}/{COMPETITOR_LAB_API_SUFFIX}0", headers=helper.IRONMAN_REQUEST_HEADER)
    try:
        total_participants = json.loads(subevent_data.text)['total']
    except KeyError as e:
        logging.error(subevent_data, subevent_data.text)
        raise e
    
    logging.info(f"Extracting data for {clab_data_id} with {total_participants} participants")
    
    competitor_data_list = []

    # Iterate through pages
    for index in range(0, total_participants, PARTICIPANTS_PER_PAGE):
        subevent_data = helper.make_request(f"{COMPETITOR_LAB_API}/{clab_data_id}/{COMPETITOR_LAB_API_SUFFIX}{index}", headers=helper.IRONMAN_REQUEST_HEADER)
        subevent_json = json.loads(subevent_data.text)
        for participant in subevent_json["data"]:
            result = {
                "Clab Event Id": clab_data_id,
                "Contact":  participant['Contact']["FullName"],
                "Gender":  participant['Contact']["Gender"],
                "Contact Id": participant["ContactId"],
                "Age Group": participant["AgeGroup"],
                "Country": participant["CountryISO2"],
                "Country Code": participant["CountryRepresentingISONumeric"],
                "Bib Number": participant["BibNumber"],
                "Event Status": participant["EventStatus"],
                "Run Time": participant["RunTimeConverted"],
                "Swim Time": participant["SwimTimeConverted"],
                "Bike Time": participant["BikeTimeConverted"],
                "Transition1 Time": participant["Transition1TimeConverted"],
                "Transition2 Time": participant["Transition2TimeConverted"],
                "Finish Time": participant["FinishTimeConverted"],
                "Finish Rank Group": participant["FinishRankGroup"],
                "Finish Rank Gender": participant["FinishRankGender"],
                "Finish Rank Overall": participant["FinishRankOverall"],
                "Swim Rank Group": participant["SwimRankGroup"],
                "Swim Rank Gender": participant["SwimRankGender"],
                "Swim Rank Overall": participant["SwimRankOverall"],
                "Bike Rank Group": participant["BikeRankGroup"],
                "Bike Rank Gender": participant["BikeRankGender"],
                "Bike Rank Overall": participant["BikeRankOverall"],
                "Run Rank Group": participant["RunRankGroup"],
                "Run Rank Gender": participant["RunRankGender"],
                "Run Rank Overall": participant["RunRankOverall"],
                "Rank Points": participant["RankPoints"],
                "Sync Date": participant["SyncDate"],
                "Result Id": participant["ResultId"]
            }
            competitor_data_list.append(result)

    logging.info(f"Extracted data for {clab_data_id} for {len(competitor_data_list)} participants")
    return competitor_data_list

def clab_extraction_handler(clab_subevent_id: str):
    """Handles the data extraction for a single subevent and saves data to csv"""
    start_time_main = time.time()
    logging.info(f"Beginning {clab_subevent_id} extraction")
    results_list = []

    # Generates a list of dictionaries
    results_list += get_clab_data(clab_subevent_id)

    logging.info(f"Total extraction time for race {clab_subevent_id} is {time.time() - start_time_main:.2f} seconds")
    pd.DataFrame(results_list).to_csv("Participant Data.csv", mode="a", header=False, index=False)

def main():
    """Main function for module"""
    helper.set_logger("get_clab_data")
    logging.info("Beginning extraction of competitor labs data")

    # Read data
    clab_data = pd.read_csv("Competitor Labs URLs.csv")
    complete_races = pd.read_csv("Participant Data.csv")["Clab Event Id"].unique()
    pending_races = []

    # Get all pending races
    for _, row in clab_data.iterrows():
        clab_subevent_id = row["Subevent Id"]
        if(clab_subevent_id not in complete_races):
            pending_races.append(clab_subevent_id)
        else:   
            logging.info(f"Already completed {clab_subevent_id}, skipping extraction")

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        executor.map(clab_extraction_handler, pending_races)

if __name__ == "__main__":
    main()
