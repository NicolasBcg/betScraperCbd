import time
from bs4 import BeautifulSoup
import requests
# Set up headless Chrome
import json
from global_func import *
from datetime import datetime, timedelta
import aiohttp
import asyncio
import re
import traceback
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
                    elif attempt>3:
                        logwrite(f"Error {response.status} fetching {url} (Retry {attempt+1}/{retries})", display_type="CONNECTION_ERROR")
                    await asyncio.sleep(2)  # Wait before retry
            except aiohttp.ClientConnectorError:
                if attempt>3:
                    logwrite(f"Connection failed: {url} (Retry {attempt+1}/{retries})", display_type="CONNECTION_ERROR")
                await asyncio.sleep(2)  # Wait before retry
            except asyncio.TimeoutError:
                if attempt>3:
                    logwrite(f"Timeout: {url} (Retry {attempt+1}/{retries})", display_type="CONNECTION_ERROR")
                await asyncio.sleep(3)  # Wait longer before retry
    return None
def is_within_4_days(timestamp):
    now = datetime.now()
    time = datetime.fromtimestamp(timestamp)
    return abs((now - time).days) <= 2

async def get_ligue(session, league_id, semaphore):
    """Fetches matches from a specific league asynchronously."""
    url = f"https://1xbet.com/LineFeed/Get1x2_VZip?sports=1&champs={league_id}&count=50&lng=en&tf=2200000&tz=7&mode=4&country=83&getEmpty=true&gr=70"
    data = await fetch_json(session, url, semaphore)
    if not data:
        return set()
    matchs = set()
    # try :
    if True:
        for match in data.get("Value", [{}]):
            ligue_name = match["L"]
            leagueName =format_name(ligue_name)
            spl=format_name(leagueName).split('-')
            adds = ""
            if 'u23' in spl:
                adds=' u23'
            elif 'u19' in spl : 
                adds=' u19'
            elif 'u20' in spl :
                adds=' u20'
            elif 'u21' in spl :
                adds=' u21'
            if 'women' in spl :
                adds+='femmes'
            match_id = match["CI"]
            team1 = match["O1"]+adds
            team2 = match["O2"]+adds
            time = match["S"]
            if is_within_4_days(time):
                url_match = f"https://1xbet.com/en/line/football/{league_id}-{format_name(ligue_name)}/{match_id}-{format_name(team1)}-{format_name(team2)}"
                matchs.add((team1, team2, url_match))
    # except :
    #     print(f"problem processing {url}")
    #     return matchs
    return matchs

async def get_matches_1xbet_async():
    """Fetches all matches from all leagues asynchronously."""
    url = "https://1xbet.com/LineFeed/GetSportsShortZip?sports=1&lng=en&tf=2200000&tz=7&country=83&virtualSports=true&gr=70&groupChamps=true"
    
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

def get_matches_1xbet():    
    return asyncio.run(get_matches_1xbet_async())
       


def get_all_bets_threader_1xbet(queue_in,queue_out,blank):
    while True :
        to_get = queue_in.get()
        if to_get == 0:
            break 
        elif to_get == -1:
            queue_out.put(blank)
        else : 
            queue_out.put(scrappe_bets_1xbet(to_get))
def format_h_val(val):
    if val == '-0.0':
        return '0'
    if int(val) == val:
        val = int(val)
    if val > 0:
        return '+'+str(val)
    else :
        return str(val)
def scrappe_bets_1xbet(match):
    team1,team2,match_url = match
    id_match = match_url.split('/')[-1].split('-')[0]
    url = f'https://1xbet.com/LineFeed/GetGameZip?id={id_match}&lng=en&isSubGames=true&GroupEvents=true&allEventsGroupSubGames=true&countevents=250&country=83&fcountry=83&marketType=1&gr=70&isNewBuilder=true'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
    else:
        logwrite(f"1xbet Error fetching {url}: {response.status_code}", display_type="CONNECTION_ERROR")
        return {}
    try:
        allbet = data['Value']['GE']
        all_bets={}  
    
        if 'P' in allbet[3]['E'][0][0].keys():
            offset = 0
        else: 
            offset = 1
        
        all_bets["1x2"]=[bet[0]['C'] for market in allbet if market["G"] == 1 for bet in market['E']]
        all_bets["doubleChance"]=[bet[0]['C'] for market in allbet if market["G"] == 8 for bet in market['E']]

        # all_bets["Both teams to score"]=[('yes',allbet[3]['E'][0][0]['C']),('no',allbet[2+offset]['E'][1][0]['C'])]
        all_bets["Total"]=[(bet['T'],bet['P'],bet['C']) for market in allbet if market["G"] == 17 for bet in market['E'][0]+market['E'][1]] #Colonne,Nbbut,Cote
        all_bets["Handicap"]=[]
        for market in allbet :
            if market["G"] == 2 or market["G"] ==2854:
                for bet in market['E'][0]+market['E'][1]:
                    if "P" in bet.keys():
                        all_bets["Handicap"].append((bet['T'],format_h_val(bet['P']),bet['C']))
                    else:
                        all_bets["Handicap"].append((bet['T'],"0",bet['C']))


    except Exception as e:
        logwrite(f"1XBET : {url} // {match_url} ERROR : {e}", display_type="CONNECTION_ERROR")
        return {}
    try : 
        bet_dict = {}
        bet_types = [('Total',"OU",format_1xbet_OverUnder),("1x2","WLD",format_1xbet_1X2),("doubleChance","doubleChance",format_1xbet_1X2_doubleChance),("Handicap","Handicap",format_1xbet_Handicap)]
        for key,bet_name,formatter in bet_types :
            if key in all_bets.keys():
                bet_dict[bet_name]= formatter(all_bets[key],team1,team2)
            else :
                bet_dict[bet_name]={}
    except Exception as e:
        logwrite(f"1XBET 2: {url} // {match_url} ERROR : {e}", display_type="CONNECTION_ERROR")
        traceback.print_exc()
        return {}
    return bet_dict


def format_1xbet_1X2(res,team1,team2):
    WLD = {}
    if len(res) == 3:
        if clean_string(team1)<=clean_string(team2):
            WLD["1"]=res[2]
            WLD["2"]=res[0]
        else:
            WLD["1"]=res[0]
            WLD["2"]=res[2]
        WLD["X"]=res[1]
    return WLD

def format_1xbet_1X2_doubleChance(res,team1,team2):
    WLD = {}
    if len(res) == 3:
        if clean_string(team1)<=clean_string(team2):
            WLD["1X"]=res[2]
            WLD["2X"]=res[0]
            WLD["12"]=res[1]
        else:
            WLD["1X"]=res[0]
            WLD["2X"]=res[2]
            WLD["12"]=res[1]
    return WLD

def format_1xbet_BTTS(res,team1,team2):#both team to score
    BTTS = {}
    for r in res:
        value = float(r[1])
        if r[0] == 'yes': 
            BTTS['Yes']=value
        elif r[0] == 'no':
            BTTS['No']=value
    return BTTS

def format_1xbet_OverUnder(res,team1,team2):
    OverUnders = {}
    for r in res:
        value = float(r[2])
        parts = r[0]
        if 9 == parts:
            OverUnders[f"O_{r[1]}"] = value
        elif 10 == parts:
            OverUnders[f"U_{r[1]}"] = value
    return OverUnders

def format_1xbet_Handicap(res,team1,team2):
    OverUnders = {}
    t1=[7,3829]
    t2=[8,3830]
    if clean_string(team1)<=clean_string(team2):
        t2= [7,3829]
        t1=[8,3830]
    for r in res:
        value = float(r[2])
        parts = r[0]
        if parts in t1:
            OverUnders[f"1_{r[1]}"] = value
        elif parts in t2:
            OverUnders[f"2_{r[1]}"] = value
    return OverUnders
# for m in get_matches_1xbet():
#     print(m)
# print(scrappe_bets_1xbet(('Lagarto', 'Uniao Atletico Carmolandense', 'https://1xbet.com/en/line/football/842973-brazil.-campeonato-brasileiro-série-d/253937821-lagarto-uniao-atletico-carmolandense')))