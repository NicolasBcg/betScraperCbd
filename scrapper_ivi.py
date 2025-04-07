from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import re
import requests
from datetime import datetime, timedelta
# Set up headless Chrome
from global_func import *
def setup_driver():
    """Set up a Selenium WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(15)
    time.sleep(5)  # Ensure we don't trigger rate limits
    return driver
# # Create a new Chrome session

import asyncio
import aiohttp
import time
from datetime import datetime, timedelta

async def is_within_4_days(time_str):
    """Check if the event time is within the next 4 days."""
    event_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    return now <= event_time <= now + timedelta(days=4)


async def fetch_json(session, url,retries = 5):
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=15) as response:  # Increased timeout
                if response.status == 200:
                    return await response.json()
                elif attempt>3:
                    print(f"Error {response.status} fetching {url} (Retry {attempt+1}/{retries})")
                await asyncio.sleep(2)  # Wait before retry
        except aiohttp.ClientConnectorError:
            if attempt>3:
                print(f"Connection failed: {url} (Retry {attempt+1}/{retries})")
            await asyncio.sleep(2)  # Wait before retry
        except asyncio.TimeoutError:
            if attempt>3:
                print(f"Timeout: {url} (Retry {attempt+1}/{retries})")
            await asyncio.sleep(3)  # Wait longer before retry
    return None

async def process_league(session, league):
    """Fetch and process event data from a single league."""
    # print(league)
    
    leagueId, leagueName = league
    addname = ""
    spl=leagueName.split('-')
    if 'u23' in spl:
        addname=' u23'
    elif 'u19' in spl : 
        addname=' u19'
    elif 'u20' in spl :
        addname=' u20'
    elif 'u21' in spl :
        addname=' u21'
    if 'women' in spl :
        addname+='femmes'
    league_url = (
        f"https://platform.ivibet.com/api/event/list?period=0&competitor1Id_neq=&competitor2Id_neq=&"
        f"status_in%5B%5D=0&limit=150&main=1&relations%5B%5D=odds&relations%5B%5D=league&relations%5B%5D=result&"
        f"relations%5B%5D=competitors&relations%5B%5D=withMarketsCount&relations%5B%5D=players&relations%5B%5D=sportCategories&"
        f"relations%5B%5D=broadcasts&relations%5B%5D=statistics&relations%5B%5D=additionalInfo&relations%5B%5D=tips&"
        f"leagueId_in%5B%5D={leagueId}&oddsExists_eq=1&lang=en"
    )

    data = await fetch_json(session, league_url)
    if not data:
        return []

    teams = {comp["id"]: comp["name"]+addname for comp in data["data"].get("relations", {}).get("competitors", [])}
    matchs = [
        (
            teams.get(m["competitor1Id"], "Unknown"),
            teams.get(m["competitor2Id"], "Unknown"),
            f"https://ivibet.com/prematch/football/{leagueId}-{leagueName}/{m['id']}-{m['translationSlug']}"
        )
        for m in data["data"].get("items", [])
        if await is_within_4_days(m["time"])
    ]

    return matchs

async def get_matches_ivi_ascync():
    """Fetch all matches using concurrent requests."""
    leagues_url = "https://platform.ivibet.com/api/v2/league/select?status=0&sport=1&period=0&orderBy=id%20asc%2C%5Border%5D%20asc&lang=en"
    
    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, leagues_url)
        if not data:
            return []
        leagues = [(league["id"], league["translationSlug"]) for league in data["data"]["leagues"]]
        print(f"Fetching {len(leagues)} leagues...")

        # Fetch league match data concurrently
        tasks = [process_league(session, league) for league in leagues]
        results = await asyncio.gather(*tasks)

    return [match for matches in results for match in matches]

def get_matches_ivi():
    return asyncio.run(get_matches_ivi_ascync())



def get_all_bets_threader_Ivi(queue_in,queue_out,blank):
    driver= setup_driver()
    while True :
        to_get = queue_in.get()
        if to_get == 0:
            driver.quit()
            break 
        elif to_get == -1:
            queue_out.put(blank)
        else : 
            r = scrape_bets_ivi(to_get)
            if r == {}:
                queue_out.put(get_bets_ivi(driver,to_get))
            else : 
                queue_out.put(r)

def scrape_bets_ivi(match):
    #https://platform.ivibet.com/api/v3/sport/config
    #621 1x2

    all_bets={}
    """Fetch and process event data from a single league."""
    team1,team2,url = match
    eventId=url.split('/')[-1].split("-")[0]
    # print("https://ivibet.com"+url)
    match_url = (

            f"https://platform.ivibet.com/api/event/list?eventId_eq={eventId}&main=0&relations%5B%5D=league&relations%5B%5D=odds"
            f"&relations%5B%5D=result&relations%5B%5D=withMarketsCount&relations%5B%5D=competitors&relations%5B%5D=sportCategories"
            f"&relations%5B%5D=players&relations%5B%5D=broadcasts&relations%5B%5D=sport&relations%5B%5D=additionalInfo&relations%5B%5D=tips&lang=en"
    )
    # print(match_url)
    response = requests.get(match_url)
    if response.status_code == 200:
        data = response.json()
    else:
        print(f"IVI Error fetching {url}: {response.status_code}")
        return {}
    if not data:
        return {}
    
    if data["data"]["items"][0]["oddsBooster"]:
        return {}
    try:
        markets = [(market["id"],market) for market in data["data"].get("relations", {}).get("odds", {}).get(str(eventId)) if market["id"] in [621,289]]
    except:
        return {}
    hcp_markets =[ market for market in
                   [market for market in data["data"].get("relations", {}).get("odds", {}).get(str(eventId)) if market["id"] if market["specifiers"]]
                   if market["specifiers"].split('=')[0]=='hcp' and market["id"] in [557,1294]
                   ]

    OUmarket = [market for mId, market in markets if mId == 289]

    ou = ['over','under']
    all_bets["289"] = [[ou[o]+" "+market["specifiers"].split("=")[-1], odds["odds"]]
                        for market in OUmarket 
                        for o, odds in enumerate(market["outcomes"])]
    
    teams=[team1,"draw",team2]
    all_bets["621"] = [[teams[o], odds["odds"]]
                        for mId,market in markets 
                        for o, odds in enumerate(market["outcomes"]) if mId == 621]
    
    teams_h = [team1,team2]
    all_bets["Handicap"] = [[teams_h[o]+" ("+format_h_val(market["specifiers"].split("=")[-1],o)+')', odds["odds"]]
                        for market in hcp_markets 
                        for o, odds in enumerate(market["outcomes"])]


    bet_types = [('289',"OU",format_ivi_OverUnder),("621","WLD",format_ivi_1X2),("Handicap","Handicap",format_ivi_Handicap)]
    bet_dict={}
    for key,bet_name,formatter in bet_types :
        if key in all_bets.keys():
            bet_dict[bet_name]= formatter(all_bets[key],team1,team2)
        else :
            bet_dict[bet_name]={}
    if bet_dict=={}:
        print("couldn't scrap bets ivi")
    return bet_dict

def format_h_val(val,team):
    if team == 1 : 
        val = str(-float(val))
    if float(val)>0:
        return '+'+val
    else : 
        return val

def get_bets_ivi(driver,match):
    
        team1,team2,url = match
        driver.get(url)
        bet_dict = {}
        market_countainers = []
        for _ in range(10):
            time.sleep(0.5)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            market_countainers = soup.find_all("div",{'data-test': 'market-countainer'})
            if market_countainers != []:
                break
            driver.execute_script("window.scrollBy(0, 50);")
        all_bets = {}
        for bet_market in market_countainers:
            market_header = bet_market.find("div", {'data-test': 'sport-event-table-market-header'})
            # Find the span within that div and get its text
            if market_header:
                bet_type = market_header.find("span").get_text(strip=True) if market_header.find("span") else None
                bets_divs = bet_market.find_all("div", {'data-test': 'sport-event-table-additional-market'})
                bets = []
                
                for div in bets_divs:
                    allspantext = [span.get_text() for span in div.find_all("span")]
                    if allspantext != []:
                        span_texts = [allspantext.pop(0)]
                    else : 
                        return {}
                    for t in allspantext :
                        span_texts.append(t.split(' '))
                    bets.append(tuple(span_texts))
                all_bets[bet_type]=bets
        if "Asian Handicap" in bet_dict.keys():
            bet_dict["Handicap"] = bet_dict["Handicap"]+bet_dict["Asian Handicap"]
        # print(soup.find_all("div",{'data-test': 'market-countainer'}))
        bet_types = [('Total',"OU",format_ivi_OverUnder),("1x2","WLD",format_ivi_1X2),("Both teams to score","BTTS",format_ivi_BTTS),("Handicap","Handicap",format_ivi_Handicap)]
        
        for key,bet_name,formatter in bet_types :
            if key in all_bets.keys():
                bet_dict[bet_name]= formatter(all_bets[key],team1,team2)
            else :
                bet_dict[bet_name]={}
        if bet_dict == {}:
            print("Couldn't get bets IVI")
        return bet_dict
    


def format_ivi_1X2(res,team1,team2):
    WLD = {}
    if clean_string(team1)<=clean_string(team2):
        tt=team1
        team1=team2
        team2=tt
    for r in res:
        try:
            value = max([float(x) for x in r if (isinstance(x, str) and x.replace('.', '', 1).isdigit()) or isinstance(x, float) or isinstance(x, int)])
            if r[0]==team1:
                WLD["1"]=value
            if r[0]==team2:
                WLD["2"]=value
            if r[0]=="draw":
                WLD["X"]=value
        except : 
            print(f'ERROR IVI 1X2 VALUE {team1},{team2}  : {r} ')
    return WLD

def format_ivi_BTTS(res,team1,team2):#both team to score
    BTTS = {}
    for r in res:
        try : 
            value = max([float(x) for x in r if (isinstance(x, str) and x.replace('.', '', 1).isdigit()) or isinstance(x, float) ])
            if r[0] == 'yes': 
                BTTS['Yes']=value
            elif r[0] == 'no':
                BTTS['No']=value
        except : 
            print(f'ERROR IVI BTTS VALUE {team1},{team2}  : {r} ')
    return BTTS

def format_ivi_OverUnder(res,team1,team2):
    OverUnders = {}
    for r in res:
        try: 
            value = max([float(x) for x in r if (isinstance(x, str) and x.replace('.', '', 1).isdigit()) or isinstance(x, float) or isinstance(x, int) ])
            parts = r[0].split()
            if "over" in parts:
                OverUnders[f"O_{parts[-1]}"] = value
            elif "under" in parts:
                OverUnders[f"U_{parts[-1]}"] = value
        except : 
            print(f'ERROR IVI OU VALUE {team1},{team2}  : {r} ')
    return OverUnders

def format_ivi_Handicap(res,team1,team2):
    HDC = {}
    if clean_string(team1)<=clean_string(team2):
        tt=team1
        team1=team2
        team2=tt
    for r in res:
        if len(r)>=1:
            parts = r[0].split()
            handicap = parts.pop(-1).strip("()")
            team = clean_string(" ".join(parts))
            if team==clean_string(team1):
                HDC[f"1_{handicap}"]=float(r[1])
            if team==clean_string(team2):
                HDC[f"2_{handicap}"]=float(r[1])
        else :
            print(f'ERROR IVI Handi VALUE {team1},{team2}  : {r}')

    return HDC


# if __name__ == "__main__":
#     start_time = time.time()
#     matches = asyncio.run(get_matches_ivi_ascync())

#     for match in matches:
#         print(match)

#     print(f"Execution time: {time.time() - start_time:.2f} seconds")

# print(scrape_bets_ivi( ('Nelson Suburbs', 'Ferrymead Bays', 'https://ivibet.com/prematch/football/1067070-new-zealand-south-premier-league/5901005-nelson-suburbs-ferrymead-bays')))