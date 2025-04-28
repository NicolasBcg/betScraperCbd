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
    retry = 0
    while retry<10:
        
        print("Waiting for Cloudflare challenge...")
        time.sleep(5)  # adjust this if needed

        # Save cookies and user-agent
        cookies = driver.get_cookies()
        
        #check id one of the cookies has a field "name" and if this field == "cf_clearance"
        if any(cookie["name"] == "cf_clearance" for cookie in cookies):
            break
        else : retry+=1
    time.sleep(10)  # adjust this if needed
    # Save cookies and user-agent
    cookies = driver.get_cookies()
    user_agent = driver.execute_script("return navigator.userAgent")
    # print(cookies)
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
        logwrite(f"Request failed: {response.status_code}")
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
    fetch_global_cookies_and_user_agent()
    """Fetches all matches from all leagues asynchronously."""
    url = "https://www.marathonbet.com/en/react/event/menu/prematch"
    cookies, user_agent = get_shared_cookies_and_user_agent()
    print("")

    semaphore = asyncio.Semaphore(8)  # Limit concurrent requests to 10
    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session,cookies, user_agent, url, semaphore)
        if not data:
            return []
        
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
       


def get_all_bets_threader_marathon(queue_in,queue_out,blank):
    cookies, user_agent = get_shared_cookies_and_user_agent()
    while True :
        to_get = queue_in.get()
        if to_get == 0:
            break 
        elif to_get == -1:
            queue_out.put(blank)
        else : 
            queue_out.put(scrappe_bets_marathon(to_get,cookies, user_agent))
def format_h_val(val):
    if val == '-0.0':
        return '0'
    if int(val) == val:
        val = int(val)
    if val > 0:
        return '+'+str(val)
    else :
        return str(val)
def scrappe_bets_marathon(match,cookies, user_agent):
    team1,team2,match_url = match
    id_match = match_url.split('/')[-1]
    url = f'https://mobile.marathonbet.com/mobile-gate/api/v1/events/tree-item?tree-id={id_match}'
    #https://mobile.marathonbet.com/mobile-gate/api/v1/events/tree-item?tree-id=22562253
    data = call_api_with_cookies(cookies, user_agent,url)
    if not data:
        # logwrite(f"marathon Error fetching {url}: {response.status_code}", display_type="CONNECTION_ERROR")
        return {}


    all_bets={}  #marketGroups
    try : 
        all_bets["1x2"]=[(data["event"]["markets"]["Match_Result"]["selections"][f"Match_Result.{res}"],res) for res in ["1","draw","3"] if f"Match_Result.{res}" in data["event"]["markets"]["Match_Result"]["selections"].keys()]
        all_bets["doubleChance"]=[(data["event"]["markets"]["Result"]["selections"][f"Result.{res}"],res) for res in ["HD","HA","AD"] if f"Result.{res}" in data["event"]["markets"]["Result"]["selections"].keys()]

        # all_bets["Both teams to score"]=[('yes',allbet[3]['E'][0][0]['C']),('no',allbet[2+offset]['E'][1][0]['C'])]
        all_bets["Total"]=[  (data["event"]["markets"][submarket]["selections"][selection])
        for market in data["event"]["marketGroups"] if market["marketGroupName"] == "TOTALS" 
        for submarket in market["marketCodes"] if len(submarket) <15 and submarket != "Total_Goals" and len(data["event"]["markets"][submarket]["selections"]) < 3 
        for selection in data["event"]["markets"][submarket]["selections"].keys()
        ]
        
        all_bets["Handicap"]= [ (data["event"]["markets"][submarket]["selections"][f"{submarket}.{res}"],res)
        for market in data["event"]["marketGroups"] if market["marketGroupName"] == "HANDICAP" 
        for submarket in market["marketCodes"] if len(submarket) <30 and len(data["event"]["markets"][submarket]["selections"]) < 3 
        for res in ["HB_H","HB_A"] 
        ]+[ (data["event"]["markets"][submarket]["selections"][f"{submarket}.{res}"],res)
        for market in data["event"]["marketGroups"] if market["marketGroupName"] == "HANDICAP" 
        for submarket in market["marketCodes"] if len(submarket) > 30
        for res in ["HB_ASN_H","HB_ASN_A"]
        ]

        
    
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
    for infos, r in res :
        if infos["selState"] == "Active": 
            value = round(float(infos["coefficient"]["price"]["numerator"]/infos["coefficient"]["price"]["denominator"]),3)+1
            if clean_string(team1)<=clean_string(team2):
                if r == '1':
                    WLD['2'] = value 
                elif r == '3':
                    WLD['1'] = value 
            else : 
                if r == '1':
                    WLD['1'] = value 
                elif r == '3':
                    WLD['2'] = value
            if r == 'draw':
                WLD['X'] = value 
    return WLD

def format_marathon_1X2_doubleChance(res,team1,team2):
    WLD = {}
    for infos, r in res :
        if infos["selState"] == "Active": 
            value = round(float(infos["coefficient"]["price"]["numerator"]/infos["coefficient"]["price"]["denominator"]),3)+1
            if clean_string(team1)<=clean_string(team2):
                if r == 'AD':
                    WLD["1X"] = value 
                elif r == 'HD':
                    WLD["2X"] = value
            else:
                if r == 'AD':
                    WLD["2X"] = value 
                elif r == 'HD':
                    WLD["1X"] = value
            if r == 'HA':
                WLD["12"]= value
    return WLD

# def format_marathon_BTTS(res,team1,team2):#both team to score
#     BTTS = {}
#     for r in res:
#         value = float(r[1])
#         if r[0] == 'yes': 
#             BTTS['Yes']=value
#         elif r[0] == 'no':
#             BTTS['No']=value
#     return BTTS

def format_marathon_OverUnder(res,team1,team2):
    OverUnders = {}
    for infos in res :
        name = infos["selName"].split(" ")
        if infos["selState"] == "Active" and "Exactly" not in name: 
            value = round(float(infos["coefficient"]["price"]["numerator"]/infos["coefficient"]["price"]["denominator"]),3)+1
            name = infos["selName"].split(" ")

            if name[0] == 'Over':
                OverUnders[f"O_{name[1]}"] = value
            elif name[0] == 'Under':
                OverUnders[f"U_{name[1]}"] = value
    return OverUnders

def format_marathon_Handicap(res,team1,team2):
    handicaps = {}
    for infos, r in res :
        if infos["selState"] == "Active": 
            value = round(float(infos["coefficient"]["price"]["numerator"]/infos["coefficient"]["price"]["denominator"]),3)+1
            handicap = format_h_val(infos["handicap"])
            if clean_string(team1)<=clean_string(team2):
                if r == 'HB_H' or r == 'HB_ASN_H':
                    handicaps[f"2_{handicap}"] = value 
                elif r == 'HB_A' or r == 'HB_ASN_A':
                    handicaps[f"1_{handicap}"] = value
            else : 
                if r == 'HB_H' or r == 'HB_ASN_H':
                    handicaps[f"1_{handicap}"] = value 
                elif r == 'HB_A' or r == 'HB_ASN_A':
                    handicaps[f"2_{handicap}"] = value

    return handicaps
# for match in get_matches_marathon() : 
#     print(match)
# cookies, user_agent = get_shared_cookies_and_user_agent()
# print(scrappe_bets_marathon(('Boston River', 'Miramar Misiones', 'https://mobile.marathonbet.com/en/sport/prematch/event/22479899'),cookies, user_agent))