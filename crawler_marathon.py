

import requests
import aiohttp
import asyncio
from global_func import *
import random
import time
import cloudscraper

# https://mobile.marathonbet.com/mobile-gate/api/v1/events/sport-highlights/flat?tree-id=11

# url = "https://www.marathonbet.com/en/react/event/menu/prematch"
# https://mobile.marathonbet.com/mobile-gate/api/v1/events/tree-item-with-children/flat?tree-id=549283&elected-markets=true
# https://mobile.marathonbet.com/mobile-gate/api/v1/events/tree-item?tree-id=22531822
# https://mobile.marathonbet.com/en/sport/prematch/event/22531822
import undetected_chromedriver as uc
import time
import requests

def preprocess_team_names(name):
    return re.sub(r'\s*\(.*?\)', '', name).lower()

def get_cookies_and_user_agent():
    options = uc.ChromeOptions()
    # options.add_argument("--headless") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-dev-shm-usage")

    driver = uc.Chrome(options=options)
    driver.get("https://mobile.marathonbet.com/")
    
    print("Waiting for Cloudflare challenge...")
    time.sleep(10)  # adjust this if needed

    # Save cookies and user-agent
    cookies = driver.get_cookies()
    user_agent = driver.execute_script("return navigator.userAgent")
    
    driver.quit()

    # Convert cookies to dict
    cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}
    return cookie_dict, user_agent

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

def get_matches_marathon():
    cookies, user_agent = get_cookies_and_user_agent()
    # url = "https://mobile.marathonbet.com/mobile-gate/api/v1/events/tree-item-with-children/flat?tree-id=549283&elected-markets=true"
    
    # data = call_api_with_cookies(cookies, user_agent,url)
    # print(data)
    url = "https://mobile.marathonbet.com/mobile-gate/api/v1/events/tree-item?tree-id=22531822"
    data = call_api_with_cookies(cookies, user_agent,url)

    print(data)

get_matches_marathon()

def process_league_marathon():
    
    if data:
        for m in data:
            leagueName = m["league"]["name"]
            
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
            if 'reserve' in spl :
                adds+=' reserve' 
            team1 = m["participants"][0]["name"]+adds
            team2 = m["participants"][1]["name"]+adds
            id_match = m["id"]
            url_match
            match.append((team1, team2, url_match,leagueName,id_match))
    return match



# print(get_matches_marathon())


def get_all_bets_threader_marathon(queue_in,queue_out,blank):
    while True :
        to_get = queue_in.get()
        if to_get == 0:
            break 
        elif to_get == -1:
            queue_out.put(blank)
        else : 
            queue_out.put(scrape_bets_marathon(to_get))

def format_price(american_odds: int) -> float:
    if american_odds > 0:
        return round((american_odds / 100) + 1, 3)
    elif american_odds < 0:
        return round((100 / abs(american_odds)) + 1, 3)
    else:
        raise ValueError("Odds cannot be zero")
def format_h_val(val,team):
    if float(val) == int(float(val)):   
        val_type = int
    else :
        val_type = float
    if team == 1 : 
        val = str(-val_type(val))
    if float(val)>0:
        return '+'+val
    else : 
        return val
def format_h_val(val):
    if val == 0:
        return '0'
    if int(val) == val:
        val = int(val)
    if val > 0:
        return '+'+str(val)
    else :
        return str(val)
    

def scrape_bets_marathon(match):
    all_bets={}
    """Fetch and process event data from a single league."""
    team1,team2,url,l_name,eventId = match
    # eventId=url.split('/')[-1]
    # print("https://ivibet.com"+url)
    match_url = f"https://guest.api.arcadia.marathon.com/0.1/matchups/{eventId}/markets/related/straight"
    # print(url)
    # print(match_url)
    #1605868082
    #https://guest.api.arcadia.marathon.com/0.1/matchups/1606931772/markets/related/straight
    #https://guest.api.arcadia.marathon.com/0.1/matchups/1605868082/markets/related/straight
    response = requests.get(match_url)
    if response.status_code == 200:
        data = response.json()
    elif response.status_code == 401:
        for _ in range(5):
            time.sleep(0.1)
            all_leagues_url = "https://guest.api.arcadia.marathon.com/0.1/sports/29/leagues?all=false&brandId=0"
            all_leagues_r = requests.get(all_leagues_url)
            if all_leagues_r.status_code == 200:
                all_leagues = all_leagues_r.json()
                for league in all_leagues:
                    if league["name"] == l_name:
                        leagueID = league["id"]
                        league_matchs = asyncio.run(asynchronisator(process_league_marathon,leagueID))
                        for team1_,team2_,url_,leagueID_,eventId_ in league_matchs: 
                            if team1_ == team1 : 
                                return scrape_bets_marathon((team1_,team2_,url_,leagueID_,eventId_))
                
            
    else:
        logwrite(url,"CONNECTION_ERROR")
        logwrite(f"marathon Error fetching {match_url}: {response.status_code}",    "CONNECTION_ERROR")
        return {}
    try : 
        if not data:
            logwrite(f"marathon No data from {match_url}: {response.status_code}","CONNECTION_ERROR")
            return {}
    except : 
        logwrite(f"marathon Error fetching data from {match_url}: {response.status_code}","CONNECTION_ERROR")
        return {}
    teams= {"home": team1,"away":team2, "draw":"draw"}
    markets = [(market["type"],market["prices"]) for market in data 
               if market["period"] == 0 and market["type"] in ["moneyline","total"]]
    
    markets_handi = []
    isSpread = False
    for market in data:
        if isSpread and market["type"]!="spread":
            break
        if market["type"]=="spread":
            isSpread = True 
            if market["period"] == 0:
                markets_handi.append(market["prices"])

    markets_ou = []
    isSpread = False
    for market in data:
        if isSpread and market["type"]!="total":
            break
        if market["type"]=="total":
            isSpread = True 
            if market["period"] == 0:
                markets_ou.append(market["prices"])

    bets = {}

    bets["WLD"] = format_marathon_1X2([[teams[price["designation"]], format_price(price["price"])] 
            for market, prices in markets if market == "moneyline"
            for price in prices if "designation" in price.keys()],team1,team2)
    
    bets["OU"] = format_marathon_OverUnder([[price["designation"],price["points"], format_price(price["price"])]
            for prices_ou in markets_ou             
            for price in prices_ou if float(price["points"]<6)],team1,team2)

    bets["Handicap"] = format_marathon_Handicap([[teams[price["designation"]],format_h_val(price["points"]), format_price(price["price"])]  
            for prices_handi in markets_handi
            for price in prices_handi],team1,team2)
    bets["doubleChance"]={}
    for bet,translation in [("1_+0.5","1X"),("2_+0.5","2X")]:
        if bet in bets["Handicap"].keys():
            bets["doubleChance"][translation]=bets["Handicap"][bet]         

    if bets["WLD"]  == {} :
        logwrite(f'ERROR {url} /// {match_url}',"CONNECTION_ERROR")
    return bets
    


def format_marathon_1X2(res,team1,team2):
    WLD = {}
    if clean_string(team1)<=clean_string(team2):
        tt=team1
        team1=team2
        team2=tt
    for r in res:
        if preprocess_team_names(r[0])==preprocess_team_names(team1):
            WLD["1"]=float(r[1])
        if preprocess_team_names(r[0])==preprocess_team_names(team2):
            WLD["2"]=float(r[1])
        if r[0]=="draw":
            WLD["X"]=float(r[1])
    return WLD

# def format_marathon_BTTS(res,team1,team2):#both team to score
#     BTTS = {}
#     for r in res:
#         if r[0] == 'Yes': 
#             BTTS['Yes']=float(r[1])
#         elif r[0] == 'No':
#             BTTS['No']=float(r[1])
#     return BTTS

def format_marathon_OverUnder(res,team1,team2):
    OverUnders = {}
    for parts in res:
        if "over" == parts[0]:
            OverUnders[f"O_{parts[1]}"] = float(parts[-1])
        elif "under" == parts[0]:
            OverUnders[f"U_{parts[1]}"] = float(parts[-1])
    return OverUnders

def format_marathon_Handicap(res,team1,team2):
    HDC = {}
    if clean_string(team1)<=clean_string(team2):
        tt=team1
        team1=team2
        team2=tt
    for r in res:
        # print(preprocess_team_names(r[0]))
        # print(preprocess_team_names(team1))
        if preprocess_team_names(r[0])==preprocess_team_names(team1):
            HDC[f"1_{r[1]}"]=float(r[-1])
        if preprocess_team_names(r[0])==preprocess_team_names(team2):
            HDC[f"2_{r[1]}"]=float(r[-1])

    return HDC


# if __name__ == "__main__":
# #     # matches = asyncio.run(get_matches_marathon_async())
# #     # print(matches)
#     print(scrape_bets_marathon(('Egersunds', 'Mjondalen', 'https://www.marathon.bet/en/soccer/norway-1st-division/egersunds-vs-mjondalen/1606508962')))