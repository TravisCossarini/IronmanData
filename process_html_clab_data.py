"""
Handles processing of HTML files extracted from Competitor labs
"""
import os
import time
import logging
from lxml import html, etree
import pandas as pd
import helper

CLAB_DATA_FOLDER = "Competitor Lab Data/"
HTML_DATA_FOLDER = "Race Data HTML/"

def print_lxml(lxml_element: html.HtmlElement):
    """
    Prints lxml elements as plain text
    """
    plain_text = etree.tostring(lxml_element, pretty_print=True, encoding='utf-8').decode('utf-8')
    print(plain_text)

def process_html_file(clab_id, file_contents) -> pd.DataFrame:
    """
    Process each html file and return a dataframe
    """
    html_parsed = html.fromstring(file_contents)
    competitor_data_list = []

    for row in html_parsed.xpath("div[@class='extraction_dummy']"):
        DNF_DESIGNATIONS = ["DNS", "DNF", "DQ", "Not Classified"]
        designation = row.xpath(".//p[text()='Designation']/preceding-sibling::p")[0].text
        dnf_flag = True if designation in DNF_DESIGNATIONS else False
        no_country_flag = True if len(row.xpath(".//div[contains(@class, 'text') and contains(@class, 'countryFlag')]/img")) == 0 else False

        competitor_data = {
            "data_source_id": clab_id,
            "Name": row.xpath(".//span")[1].text,
            "Designation": designation,
            "Div Rank" : row.xpath(".//p[text()='Div Rank']/preceding-sibling::p")[0].text if not dnf_flag else "",
            "Gender Rank": row.xpath(".//p[text()='Gender Rank']/preceding-sibling::p")[0].text if not dnf_flag else "",
            "Overall Rank": row.xpath(".//p[text()='Overall Rank']/preceding-sibling::p")[0].text if not dnf_flag else "",
            "Bib": row.xpath(".//div[contains(@class, 'tableRow') and contains(@class, 'tableFooter')]/div/div")[0].text,
            "Division": row.xpath(".//div[contains(@class, 'tableRow') and contains(@class, 'tableFooter')]/div/div")[1].text,
            "Country": row.xpath(".//div[contains(@class, 'text') and contains(@class, 'countryFlag')]/img")[0].get("alt") if not no_country_flag else "",
            "Points": row.xpath(".//div[contains(@class, 'tableRow') and contains(@class, 'tableFooter')]/div/div")[3].text,
            "Swim Time": row.xpath(".//div[contains(@id, 'swimDetails')]/div/div/div/div")[4].text,
            "Swim Div Rank": row.xpath(".//div[contains(@id, 'swimDetails')]/div/div/div/div")[5].text,
            "Swim Gender Rank": row.xpath(".//div[contains(@id, 'swimDetails')]/div/div/div/div")[6].text,
            "Swim Overall Rank": row.xpath(".//div[contains(@id, 'swimDetails')]/div/div/div/div")[7].text,
            "Bike Time": row.xpath(".//div[contains(@id, 'bikeDetails')]/div/div/div/div")[4].text,
            "Bike Div Rank": row.xpath(".//div[contains(@id, 'bikeDetails')]/div/div/div/div")[5].text,
            "Bike Gender Rank": row.xpath(".//div[contains(@id, 'bikeDetails')]/div/div/div/div")[6].text,
            "Bike Overall Rank": row.xpath(".//div[contains(@id, 'bikeDetails')]/div/div/div/div")[7].text,
            "Run Time": row.xpath(".//div[contains(@id, 'runDetails')]/div/div/div/div")[4].text,
            "Run Div Rank": row.xpath(".//div[contains(@id, 'runDetails')]/div/div/div/div")[5].text,
            "Run Gender Rank": row.xpath(".//div[contains(@id, 'runDetails')]/div/div/div/div")[6].text,
            "Run Overall Rank": row.xpath(".//div[contains(@id, 'runDetails')]/div/div/div/div")[7].text,
            "Transition 1": row.xpath(".//div[contains(@id, 'transitions')]/div/div/div/div")[2].text,
            "Transition 2": row.xpath(".//div[contains(@id, 'transitions')]/div/div/div/div")[3].text,
            "Overall Time": row.xpath(".//div[contains(@class, 'summaryRow') and contains(@class, 'overallRow')]/p[contains(@class, 'summaryTime')]")[0].text
        }
        competitor_data_list.append(competitor_data)
    return pd.DataFrame(competitor_data_list)
        

def main():
    """
    Main function, facilitates extraction of all HTML files
    """
    helper.set_logger("HTML_Extraction")
    html_files_list = os.listdir(r"./Race Data HTML")

    for html_file in html_files_list:
        start_time = time.time()
        with open(f"{HTML_DATA_FOLDER}{html_file}", "r", encoding="utf-8") as file:
            file_contents = file.read()
            process_html_file(html_file[:-5], file_contents).to_csv(f"{CLAB_DATA_FOLDER}{html_file[:-5]}.csv", index=False)
        logging.info(f"HTML Extraction time for file {html_file[:-5]} is: {time.time() - start_time:.2f}")

if __name__ == "__main__":
    main()