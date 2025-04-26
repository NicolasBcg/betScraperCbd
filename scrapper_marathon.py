import requests
from global_func import *
import aiohttp
import asyncio
import re
import traceback
import undetected_chromedriver as uc
import time
# Precompile regex for efficiency
format_regex = re.compile(r'\s*-\s*')

def get_cookies_and_user_agent():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    # options.add_argument("--headless") 
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options)
    driver.get("https://mobile.marathonbet.com/")
    cookies = driver.get_cookies()
    while len(cookies) == 0:
        
        print("Waiting for Cloudflare challenge...")
        time.sleep(5)  # adjust this if needed

        # Save cookies and user-agent
        cookies = driver.get_cookies()
    time.sleep(10)  # adjust this if needed
    # Save cookies and user-agent
    cookies = driver.get_cookies()
    user_agent = driver.execute_script("return navigator.userAgent")
    driver.quit()
    

    # Convert cookies to dict
    cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
    return cookie_dict, user_agent
    
def format_name(name):
    """Formats a name to be URL-friendly."""
    return format_regex.sub('-', name.lower().replace(" ", "-"))


def call_api_with_cookies(cookies, user_agent,url):
    headers = {
        "User-Agent": user_agent,
        "Referer": "https://mobile.marathonbet.com/",
        "Accept": "application/json, text/plain, */*"
    }

    response = requests.get(url, headers=headers, cookies=cookies)

    if response.ok:
        return response.json()
    else:
        print(f"Request failed: {response.status_code}")
        return None
    
async def fetch_json(session,cookies, user_agent, url, semaphore, retries=5):
    headers = {
        "User-Agent": user_agent,
        "Referer": "https://mobile.marathonbet.com/",
        "Accept": "application/json, text/plain, */*"
    }
    """Fetch JSON data asynchronously with retries and timeout handling."""
    async with semaphore:
        for attempt in range(retries):
            try:
                async with session.get(url, headers=headers, cookies=cookies, timeout=15) as response:  # Increased timeout
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


def find_event_children(node, results=None):
    if results is None:
        results = []

    # If the node has eventInfo, store it
    if "eventInfo" in node:
        results.append(node)

    # Traverse children if they exist
    children = node.get("catInfo", {}).get("children", [])
    for child in children:
        find_event_children(child, results)

    return results

async def get_ligue(session,cookies, user_agent, league_id,league_url, semaphore):
    """Fetches matches from a specific league asynchronously."""
    url = f"https://mobile.marathonbet.com/mobile-gate/api/v1/events/tree-item-with-children/flat?tree-id={league_id}&elected-markets=true"

    data = await fetch_json(session,cookies, user_agent, url, semaphore)
    if not data:
        return set()
    # print('fetched')
    matchs = set()
    spl=league_url.lower().replace("-", "").replace(".", "").replace("/", "+").split('+')
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
    # try :
    for match in find_event_children(data):
        match_id = match["treeId"]
        matchName = match["name"]   
        if len(matchName.split(" vs "))==2:
            team1 = matchName.split(" vs ")[0]
            team2 = matchName.split(" vs ")[1]
            match_start = match["eventInfo"]["displayTime"]
            # print(match_start)
            if is_within_4_days(match_start):
                url_match = f"https://mobile.marathonbet.com/en/sport/prematch/event/{match_id}"
                matchs.add((team1, team2, url_match))
                # print(f"found {team1} vs {team2} at {match_start}")
            # else : 
                # print(f"not in time {match_start}")
                                
# except :
#     print(f"problem processing {url}")
    return matchs


async def get_matches_marathon_async():
    """Fetches all matches from all leagues asynchronously."""
    url = "https://www.marathonbet.com/en/react/event/menu/prematch"
    cookies, user_agent = get_cookies_and_user_agent()
    semaphore = asyncio.Semaphore(8)  # Limit concurrent requests to 10
    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session,cookies, user_agent, url, semaphore)
        if not data:
            return set()
        
        ligues = [(ligue["uid"],ligue["url"]) for sport in data["childs"] if sport["label"] == 'Football' 
                  for country in sport["childs"] 
                  for ligue in country["childs"]]

        call_api_with_cookies(cookies, user_agent,url)
        # Fetch all league matches concurrently
        tasks = [get_ligue(session,cookies, user_agent, league_id,league_url, semaphore) for league_id,league_url in ligues]
        results = await asyncio.gather(*tasks)

        all_matches = set()
        for result in results:
            all_matches.update(result)
    
    return list(all_matches)

def get_matches_marathon():    
    return asyncio.run(get_matches_marathon_async())
       
for match in get_matches_marathon() : 
    print(match)

def get_all_bets_threader_marathon(queue_in,queue_out,blank):
    while True :
        to_get = queue_in.get()
        if to_get == 0:
            break 
        elif to_get == -1:
            queue_out.put(blank)
        else : 
            queue_out.put(scrappe_bets_marathon(to_get))
def format_h_val(val):
    if val == '-0.0':
        return '0'
    if int(val) == val:
        val = int(val)
    if val > 0:
        return '+'+str(val)
    else :
        return str(val)
def scrappe_bets_marathon(match):
    team1,team2,match_url = match
    id_match = match_url.split('/')[-1].split('-')[0]
    url = f'https://marathon.com/LineFeed/GetGameZip?id={id_match}&lng=en&isSubGames=true&GroupEvents=true&allEventsGroupSubGames=true&countevents=250&country=83&fcountry=83&marketType=1&gr=70&isNewBuilder=true'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
    else:
        logwrite(f"marathon Error fetching {url}: {response.status_code}", display_type="CONNECTION_ERROR")
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
        logwrite(f"marathon : {url} // {match_url} ERROR : {e}", display_type="CONNECTION_ERROR")
        return {}
    try : 
        bet_dict = {}
        bet_types = [('Total',"OU",format_marathon_OverUnder),("1x2","WLD",format_marathon_1X2),("doubleChance","doubleChance",format_marathon_1X2_doubleChance),("Handicap","Handicap",format_marathon_Handicap)]
        for key,bet_name,formatter in bet_types :
            if key in all_bets.keys():
                bet_dict[bet_name]= formatter(all_bets[key],team1,team2)
            else :
                bet_dict[bet_name]={}
    except Exception as e:
        logwrite(f"marathon 2: {url} // {match_url} ERROR : {e}", display_type="CONNECTION_ERROR")
        traceback.print_exc()
        return {}
    return bet_dict


def format_marathon_1X2(res,team1,team2):
    WLD = {}
    if len(res) == 3:
        if clean_string(team1)<=clean_string(team2):
            WLD["1"]=res[2] * 0.91
            WLD["2"]=res[0] * 0.91
        else: 
            WLD["1"]=res[0] * 0.91
            WLD["2"]=res[2] * 0.91
        WLD["X"]=res[1] * 0.91
    return WLD

def format_marathon_1X2_doubleChance(res,team1,team2):
    WLD = {}
    if len(res) == 3:
        if clean_string(team1)<=clean_string(team2):
            WLD["1X"]=res[2] * 0.91
            WLD["2X"]=res[0] * 0.91
            WLD["12"]=res[1] * 0.91
        else:
            WLD["1X"]=res[0] * 0.91
            WLD["2X"]=res[2] * 0.91
            WLD["12"]=res[1] * 0.91
    return WLD

def format_marathon_BTTS(res,team1,team2):#both team to score
    BTTS = {}
    for r in res:
        value = float(r[1])
        if r[0] == 'yes': 
            BTTS['Yes']=value
        elif r[0] == 'no':
            BTTS['No']=value
    return BTTS

def format_marathon_OverUnder(res,team1,team2):
    OverUnders = {}
    for r in res:
        value = float(r[2])
        parts = r[0]
        if 9 == parts:
            OverUnders[f"O_{r[1]}"] = value * 0.91
        elif 10 == parts:
            OverUnders[f"U_{r[1]}"] = value * 0.91
    return OverUnders

def format_marathon_Handicap(res,team1,team2):
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
            OverUnders[f"1_{r[1]}"] = value * 0.91
        elif parts in t2:
            OverUnders[f"2_{r[1]}"] = value * 0.91
    return OverUnders
# for m in get_matches_marathon():
#     print(m)
# print(scrappe_bets_marathon(('Lagarto', 'Uniao Atletico Carmolandense', 'https://marathon.com/en/line/football/842973-brazil.-campeonato-brasileiro-série-d/253937821-lagarto-uniao-atletico-carmolandense')))