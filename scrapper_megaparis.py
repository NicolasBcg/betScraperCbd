import time
from bs4 import BeautifulSoup
import requests
# Set up headless Chrome
import json
from global_func import *

import aiohttp
import asyncio
import re

# Precompile regex for efficiency
format_regex = re.compile(r'\s*-\s*')

def format_name(name):
    """Formats a name to be URL-friendly."""
    return format_regex.sub('-', name.lower().replace(" ", "-"))

async def fetch_json(session, url, semaphore, retries=5):
    """Fetch JSON data asynchronously with retries and timeout handling."""
    async with semaphore:
        for attempt in range(retries):
            try:
                async with session.get(url, timeout=15) as response:  # Increased timeout
                    if response.status == 200:
                        return await response.json()
                    print(f"Error {response.status} fetching {url}")
                    await asyncio.sleep(2)  # Wait before retry
            except aiohttp.ClientConnectorError:
                print(f"Connection failed: {url} (Retry {attempt+1}/{retries})")
                await asyncio.sleep(2)  # Wait before retry
            except asyncio.TimeoutError:
                print(f"Timeout: {url} (Retry {attempt+1}/{retries})")
                await asyncio.sleep(3)  # Wait longer before retry
    return None

async def get_ligue(session, league_id, semaphore):
    """Fetches matches from a specific league asynchronously."""
    url = f"https://megapari.com/service-api/LineFeed/GetSportsShortZip?sports=1&champs={league_id}&lng=en&country=83&partner=192&virtualSports=true&gr=824&groupChamps=true"
    
    data = await fetch_json(session, url, semaphore)
    if not data:
        return set()
    
    matchs = set()
    for ligue in data.get("Value", [{}])[0].get("L", []):
        if "G" in ligue:
            ligue_name = ligue["L"]
            for match in ligue["G"]:
                match_id = match["CI"]
                team1 = match["O1"]
                team2 = match["O2"]
                url_match = f"https://megapari.com/en/line/football/{league_id}-{format_name(ligue_name)}/{match_id}-{format_name(team1)}-{format_name(team2)}"
                matchs.add((team1, team2, url_match))
    
    return matchs

async def get_matches_mega_async():
    """Fetches all matches from all leagues asynchronously."""
    url = "https://megapari.com/service-api/LineFeed/GetSportsShortZip?sports=1&lng=en&country=83&partner=192&virtualSports=true&gr=824&groupChamps=true"
    
    semaphore = asyncio.Semaphore(10)  # Limit concurrent requests to 10
    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url, semaphore)
        if not data:
            return set()
        
        ligues = {l["LI"] for lig in data.get("Value", [{}])[0].get("L", []) for l in lig.get("SC", [{"LI": lig["LI"]}])}

        # Fetch all league matches concurrently
        tasks = [get_ligue(session, league_id, semaphore) for league_id in ligues]
        results = await asyncio.gather(*tasks)

        all_matches = set()
        for result in results:
            all_matches.update(result)

    return all_matches

def get_matches_mega():    
    return asyncio.run(get_matches_mega_async())
       


def get_all_bets_threader_Mega(queue_in,queue_out,blank):
    while True :
        to_get = queue_in.get()
        if to_get == 0:
            break 
        elif to_get == -1:
            queue_out.put(blank)
        else : 
            queue_out.put(scrappe_bets_mega(to_get))
def scrappe_bets_mega(match):
    team1,team2,match_url = match
    id_match = match_url.split('/')[-1].split('-')[0]
    url = f'https://megapari.com/service-api/LineFeed/GetGameZip?id={id_match}&lng=en&isSubGames=true&GroupEvents=true&countevents=250&grMode=4&partner=192&topGroups=&country=83&marketType=1'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
    else:
        print(f"Megaparis Error fetching {url}: {response.status_code}")
        return []
    try:  
        allbet = data['Value']['GE']
        all_bets={}  
    
        if 'P' in allbet[3]['E'][0][0].keys():
            offset = 0
        else: 
            offset = 1
   
        all_bets["1x2"]=[bet[0]['C'] for bet in allbet[0]['E']]
        all_bets["Both teams to score"]=[('yes',allbet[3]['E'][0][0]['C']),('no',allbet[2+offset]['E'][1][0]['C'])]
        all_bets["Total"]=[(bet['T'],bet['P'],bet['C']) for bet in allbet[3+offset]['E'][0]+allbet[3+offset]['E'][1]] #Colonne,Nbbut,Cote
    except Exception as e:
        print(f"MEGAPARIS : {url} // {match_url} ERROR : {e}")
        return {}

    bet_dict = {}
    bet_types = [('Total',"OU",format_mega_OverUnder),("1x2","WLD",format_mega_1X2),("Both teams to score","BTTS",format_mega_BTTS)]
    for key,bet_name,formatter in bet_types :
        if key in all_bets.keys():
            bet_dict[bet_name]= formatter(all_bets[key],team1,team2)
        else :
            bet_dict[bet_name]={}
    return bet_dict


def format_mega_1X2(res,team1,team2):
    WLD = {}
    if clean_string(team1)<=clean_string(team2):
        WLD["1"]=res[2]
        WLD["2"]=res[0]
    else:
        WLD["1"]=res[0]
        WLD["2"]=res[2]
    WLD["X"]=res[1]
    return WLD

def format_mega_BTTS(res,team1,team2):#both team to score
    BTTS = {}
    for r in res:
        value = float(r[1])
        if r[0] == 'yes': 
            BTTS['Yes']=value
        elif r[0] == 'no':
            BTTS['No']=value
    return BTTS

def format_mega_OverUnder(res,team1,team2):
    OverUnders = {}
    for r in res:
        value = float(r[2])
        parts = r[0]
        if 9 == parts:
            OverUnders[f"O_{r[1]}"] = value
        elif 10 == parts:
            OverUnders[f"U_{r[1]}"] = value
    return OverUnders
# print(scrappe_bets_mega(('Bodo-Glimt', 'Lazio', 'https://megapari.com/en/line/football/118593-uefa-europa-league/252984638-bodo-glimt-lazio')))