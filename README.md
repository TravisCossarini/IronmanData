# IronmanData
Purpose: Download all race data from the Ironman website.

## Data Structure on Ironman Website
The Ironman website stores data for all future and historic races by location (referred to as "Races" from here on out). All data for races is stored in a secondary website called Competitor Labs. Within each Race there are subevents on Competitor Labs, one for each year and type (open division, regular, triclub).

## Script Structure
Execution is handled by several component scripts:
1. get_race_information.py - Retrieves all Races by ID from the Ironman website
2. get_clab_ids.py - For each race, gets all child competitor lab subevent ids
3. get_clab_data.py - For each subevent id, retrieve all participant data

This outputs the following files:
1. Race Information.csv - Contains the id's and information about the conditions at each race from the Ironman website
2. Competitor Labs Subevents.csv - Contains the list of subevents for each race including their Competitor Labs ID
3. Participant Data.csv - Contains all data from each Competitor Labs subevent

Ensure to use a VPN to avoid IP banning when executing.

# TODO
Download and analyze the race tracks for elevation etc.