import requests
from datetime import datetime, timedelta
import aiohttp
import asyncio
from global_func import *
import random
import time
def preprocess_team_names(name):
    return re.sub(r'\s*\(.*?\)', '', name).lower()

# def is_within_4_days(cutoff_str):
#     # Convertir la date du JSON en objet datetime
#     cutoff_dt = datetime.strptime(cutoff_str, "%Y-%m-%dT%H:%M:%SZ")
    
#     # Obtenir la date actuelle en UTC
#     now = datetime.now()
#     # Vérifier si la date est dans moins de 4 jours
#     return now <= cutoff_dt <= now + timedelta(days=4)

#https://guest.api.arcadia.pinnacle.com/0.1/leagues/{league}/matchups?brandId=0
#https://guest.api.arcadia.pinnacle.com/0.1/sports/29/leagues?all=false&brandId=0
def format_name(str):
    # Convert to lowercase
    str = str.lower()
    # Replace non-alphanumeric characters (like " - ") with a hyphen
    str = re.sub(r'\s*-\s*', '-', str)
    # Replace spaces with hyphens
    str = str.replace(" ", "-")
    return str
def contains_keywords(text):
    keywords = {"draw", "over", "under","odd","even" "even", "yes", "no", "1", "0","+", "-","corners" , "bookings"}
    return any(word.lower() in text.lower() for word in keywords)




async def fetch_json(session, url,retries = 5):
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=15) as response:  # Increased timeout
                if response.status == 200:
                    return await response.json()
                elif attempt>3:
                    logwrite(f"Error {response.status} fetching {url} (Retry {attempt+1}/{retries})","CONNECTION_ERROR")
                if retries!=1:
                    await asyncio.sleep(random.uniform(2, 4))  # Wait before retry
        except aiohttp.ClientConnectorError:
            if attempt>3:
                logwrite(f"Connection failed: {url} (Retry {attempt+1}/{retries})","CONNECTION_ERROR")
            await asyncio.sleep(random.uniform(2, 4))  # Wait before retry
        except asyncio.TimeoutError:
            if attempt>3:
                logwrite(f"Timeout: {url} (Retry {attempt+1}/{retries})","CONNECTION_ERROR")
            await asyncio.sleep(random.uniform(2, 4))  # Wait longer before retry
    return None

async def process_league_pinnacle(session, leagueID):
    url = f"https://guest.api.arcadia.pinnacle.com/0.1/leagues/{leagueID}/matchups?brandId=0"#9320
    #https://guest.api.arcadia.pinnacle.com/0.1/leagues/9320/matchups?brandId=0
    data = await fetch_json(session, url)
    
    match = []
    if data:
        for m in data:
            leagueName = m["league"]["name"]
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
            if 'reserve' in spl :
                adds+=' reserve' 
            team1 = m["participants"][0]["name"]+adds
            team2 = m["participants"][1]["name"]+adds
            id_match = m["id"]
            
            # url_match = f"https://www.pinnacle.bet/en/soccer/{format_name(leagueName)}/{format_name(team1)}-vs-{format_name(team2)}/{id_match}"
            url_match = f"https://www.pinnacle.com/en/soccer/{format_name(leagueName)}/matchups/#all"
            if not contains_keywords(team1) and await is_within_4_days_async(m["startTime"],website='pinnacle'):
                resp = await fetch_json(session,f"https://guest.api.arcadia.pinnacle.com/0.1/matchups/{id_match}/markets/related/straight",retries=1)
                if resp != {} and resp != None:
                    match.append((team1, team2, url_match,leagueName,id_match))
    return match

async def get_matches_pinnacle_async():
    url = "https://guest.api.arcadia.pinnacle.com/0.1/sports/29/leagues?all=false&brandId=0"
    
    async with aiohttp.ClientSession() as session:
        data = await fetch_json(session, url)
        if not data:
            return []
        
        # Process leagues concurrently
        tasks = [process_league_pinnacle(session, l["id"]) for l in data]
        results = await asyncio.gather(*tasks)
        
        # Flatten the list
        matches = [match for sublist in results for match in sublist]
    
    return matches
def get_matches_pinnacle():
    return asyncio.run(get_matches_pinnacle_async())


def get_all_bets_threader_Pinnacle(queue_in,queue_out,blank):
    while True :
        to_get = queue_in.get()
        if to_get == 0:
            break 
        elif to_get == -1:
            queue_out.put(blank)
        else : 
            queue_out.put(scrape_bets_pinnacle(to_get))

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

async def asynchronisator(func,arg):
    async with aiohttp.ClientSession() as session:
        return await func(session, arg)
    

def scrape_bets_pinnacle(match):
    all_bets={}
    """Fetch and process event data from a single league."""
    team1,team2,url,l_name,eventId = match
    # eventId=url.split('/')[-1]
    # print("https://ivibet.com"+url)
    match_url = f"https://guest.api.arcadia.pinnacle.com/0.1/matchups/{eventId}/markets/related/straight"
    # print(url)
    # print(match_url)
    #1605868082
    #https://guest.api.arcadia.pinnacle.com/0.1/matchups/1606931772/markets/related/straight
    #https://guest.api.arcadia.pinnacle.com/0.1/matchups/1605868082/markets/related/straight
    response = requests.get(match_url)
    if response.status_code == 200:
        data = response.json()
    elif response.status_code == 401:
        for _ in range(5):
            time.sleep(0.1)
            all_leagues_url = "https://guest.api.arcadia.pinnacle.com/0.1/sports/29/leagues?all=false&brandId=0"
            all_leagues_r = requests.get(all_leagues_url)
            if all_leagues_r.status_code == 200:
                all_leagues = all_leagues_r.json()
                for league in all_leagues:
                    if league["name"] == l_name:
                        leagueID = league["id"]
                        league_matchs = asyncio.run(asynchronisator(process_league_pinnacle,leagueID))
                        for team1_,team2_,url_,leagueID_,eventId_ in league_matchs: 
                            if team1_ == team1 : 
                                return scrape_bets_pinnacle((team1_,team2_,url_,leagueID_,eventId_))
                
            
    else:
        logwrite(url,"CONNECTION_ERROR")
        logwrite(f"Pinnacle Error fetching {match_url}: {response.status_code}",    "CONNECTION_ERROR")
        return {}
    try : 
        if not data:
            logwrite(f"Pinnacle No data from {match_url}: {response.status_code}","CONNECTION_ERROR")
            return {}
    except : 
        logwrite(f"Pinnacle Error fetching data from {match_url}: {response.status_code}","CONNECTION_ERROR")
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

    bets["WLD"] = format_pinnacle_1X2([[teams[price["designation"]], format_price(price["price"])] 
            for market, prices in markets if market == "moneyline"
            for price in prices if "designation" in price.keys()],team1,team2)
    
    bets["OU"] = format_pinnacle_OverUnder([[price["designation"],price["points"], format_price(price["price"])]
            for prices_ou in markets_ou             
            for price in prices_ou if float(price["points"]<6)],team1,team2)

    bets["Handicap"] = format_pinnacle_Handicap([[teams[price["designation"]],format_h_val(price["points"]), format_price(price["price"])]  
            for prices_handi in markets_handi
            for price in prices_handi],team1,team2)
    bets["doubleChance"]={}
    for bet,translation in [("1_+0.5","1X"),("2_+0.5","2X")]:
        if bet in bets["Handicap"].keys():
            bets["doubleChance"][translation]=bets["Handicap"][bet]         

    if bets["WLD"]  == {} :
        logwrite(f'ERROR {url} /// {match_url}',"CONNECTION_ERROR")
    return bets
    


def format_pinnacle_1X2(res,team1,team2):
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

# def format_pinnacle_BTTS(res,team1,team2):#both team to score
#     BTTS = {}
#     for r in res:
#         if r[0] == 'Yes': 
#             BTTS['Yes']=float(r[1])
#         elif r[0] == 'No':
#             BTTS['No']=float(r[1])
#     return BTTS

def format_pinnacle_OverUnder(res,team1,team2):
    OverUnders = {}
    for parts in res:
        if "over" == parts[0]:
            OverUnders[f"O_{parts[1]}"] = float(parts[-1])
        elif "under" == parts[0]:
            OverUnders[f"U_{parts[1]}"] = float(parts[-1])
    return OverUnders

def format_pinnacle_Handicap(res,team1,team2):
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


if __name__ == "__main__":
#     # matches = asyncio.run(get_matches_pinnacle_async())
#     # print(matches)
    print(scrape_bets_pinnacle(('Egersunds', 'Mjondalen', 'https://www.pinnacle.bet/en/soccer/norway-1st-division/egersunds-vs-mjondalen/1606508962')))