import requests
from datetime import datetime, timedelta
import aiohttp
import asyncio
from global_func import *


def preprocess_team_names(name):
    return re.sub(r'\s*\(.*?\)', '', name).lower()

def is_within_4_days(cutoff_str):
    # Convertir la date du JSON en objet datetime
    cutoff_dt = datetime.strptime(cutoff_str, "%Y-%m-%dT%H:%M:%SZ")
    
    # Obtenir la date actuelle en UTC
    now = datetime.now()
    # Vérifier si la date est dans moins de 4 jours
    return now <= cutoff_dt <= now + timedelta(days=4)

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




async def fetch_json(session, url,ignore_error = False):
    async with session.get(url) as response:
        if response.status == 200:
            return await response.json()
        elif ignore_error :
            return {}
        else:
            print(f"Error: {response.status}")
            return None

async def process_league_pinnacle(session, leagueID):
    url = f"https://guest.api.arcadia.pinnacle.com/0.1/leagues/{leagueID}/matchups?brandId=0"#9320
    #https://guest.api.arcadia.pinnacle.com/0.1/leagues/9320/matchups?brandId=0
    data = await fetch_json(session, url)
    
    match = []
    if data:
        for m in data:
            team1 = m["participants"][0]["name"]
            team2 = m["participants"][1]["name"]
            id_match = m["id"]
            leagueName = m["league"]["name"]
            url_match = f"https://www.pinnacle.bet/en/soccer/{format_name(leagueName)}/{format_name(team1)}-vs-{format_name(team2)}/{id_match}"
            
            if not contains_keywords(team1) and is_within_4_days(m["periods"][0]["cutoffAt"]):
                resp = await fetch_json(session,f"https://guest.api.arcadia.pinnacle.com/0.1/matchups/{id_match}/markets/related/straight",ignore_error=True)
                if resp != {}:
                    match.append((team1, team2, url_match))

    
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
    
def format_h_val(val):
    if val == 0:
        return '0'
    if int(val) == val:
        val = int(val)
    if val > 0:
        return '+'+str(val)
    else :
        return str(val)


def scrape_bets_pinnacle(match):
    all_bets={}
    """Fetch and process event data from a single league."""
    team1,team2,url = match
    eventId=url.split('/')[-1]
    # print("https://ivibet.com"+url)
    match_url = (f"https://guest.api.arcadia.pinnacle.com/0.1/matchups/{eventId}/markets/related/straight")
    # print(url)
    # print(match_url)
    #1605868082
    #https://guest.api.arcadia.pinnacle.com/0.1/matchups/1606931772/markets/related/straight
    #https://guest.api.arcadia.pinnacle.com/0.1/matchups/1605868082/markets/related/straight
    response = requests.get(match_url)
    if response.status_code == 200:
        data = response.json()
    else:
        
        print(f"Pinnacle Error fetching {match_url}: {response.status_code}")
        return {}
    if not data:
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


    bets = {}

    bets["WLD"] = format_pinnacle_1X2([[teams[price["designation"]], format_price(price["price"])] 
            for market, prices in markets if market == "moneyline"
            for price in prices if "designation" in price.keys()],team1,team2)
    bets["OU"] = format_pinnacle_OverUnder([[price["designation"],price["points"], format_price(price["price"])] 
            for market, prices in markets if market == "total" 
            for price in prices if float(price["points"]<6)],team1,team2)

    bets["Handicap"] = format_pinnacle_Handicap([[teams[price["designation"]],format_h_val(price["points"]), format_price(price["price"])]  
            for prices_handi in markets_handi
            for price in prices_handi],team1,team2)
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