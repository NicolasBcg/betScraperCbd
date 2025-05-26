from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import requests
import time
import re
import threading
from queue import Queue
from datetime import datetime, timedelta
import aiohttp
import asyncio

# Set up Selenium with headless Chrome
def setup_driver():
    """Set up a Selenium WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")

    # chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    time.sleep(5)  # Ensure we don't trigger rate limits
    return driver

def preprocess_team_names(name):
    return re.sub(r'\s*\(.*?\)', '', name).lower()

def is_within_4_days(cutoff_str):
    # Convertir la date du JSON en objet datetime
    cutoff_dt = datetime.strptime(cutoff_str, "%Y-%m-%dT%H:%M:%SZ")
    
    # Obtenir la date actuelle en UTC
    now = datetime.utcnow()
    
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
    url = f"https://guest.api.arcadia.pinnacle.com/0.1/leagues/{leagueID}/matchups?brandId=0"
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




def clean_string(s):
    # Remove unwanted patterns
    s= s.lower()
    s = re.sub(r'afc|ac|fc|as|vfl|vfb|\s|fsv|tsg|rb|-|\b\d+\.\b|\d+| i | ii ', '', s)
    # Convert to lowercase and remove spaces
    return s.replace(" ", "")

def get_all_bets_Pinnacle(common,blank):
    r = []
    driver= setup_driver()
    for tPinnacle in common:
        if tPinnacle!=-1:
            r.append(get_bets_pinnacle(driver,tPinnacle))  # Replace with desired team names
        else : 
            r.append(blank) 
    return r

def get_all_bets_threader_Pinnacle(queue_in,queue_out,blank):
    driver= setup_driver()
    while True :
        to_get = queue_in.get()
        if to_get == 0:
            driver.quit()
            break 
        elif to_get == -1:
            queue_out.put(blank)
        else : 
            queue_out.put(get_bets_pinnacle(driver,to_get))

def get_bets_pinnacle(driver, match):
    team1,team2,base_url = match
    # ,("Both Teams To Score","BTTS",format_pinnacle_BTTS)
    url = base_url+'/#period:0'
    bet_types = [('Money Line – Match',"WLD",format_pinnacle_1X2),('Total – Match',"OU",format_pinnacle_OverUnder),('Handicap – Match',"Handicap",format_pinnacle_Handicap)]
    res = get_odds_from_page(driver,url,bet_types,team1,team2)
    driver.get('https://www.google.com/')
    time.sleep(0.5)
    url = base_url+'/#period:1'
    bet_types = [('Total – 1st Half',"OU",format_pinnacle_OverUnder),('Money Line – 1st Half',"WLD",format_pinnacle_1X2)]
    res1half = get_odds_from_page(driver,url,bet_types,team1,team2)
    driver.get('https://www.google.com/')
    time.sleep(0.5)
    url = base_url+'/#team-props'
    bet_types = [('Both Teams To Score? 1st Half',"BTTS1F",format_pinnacle_BTTS),('Both Teams To Score?',"BTTS",format_pinnacle_BTTS)]
    btts = get_odds_from_page(driver,url,bet_types,team1,team2)
    for type_b in ["OU","WLD"] : 
        for key in res1half[type_b].keys():
            res[type_b]["1st_Half_"+key]=res1half[type_b][key]
    try:
        res["BTTS"]=btts["BTTS"]

        for key in btts["BTTS1F"].keys():
            res["BTTS"]["1st_Half_"+key]=btts["BTTS1F"][key]
    except: 
        pass
    return res



def get_odds_from_page(driver,url,bet_types,team1,team2):
    result = {}
    driver.get(url)
    # print(url)
    # Wait for the dynamic content to load (adjust time as needed or use explicit waits)
    bet_type,normalized_bet_type,formatfunc = bet_types[0]
    for _ in range(10):
        html = driver.page_source
        # print(html)
        soup = BeautifulSoup(html, "html.parser")
        time.sleep(1)
        target_div = soup.find('span', string=lambda text: text and text == bet_type )
        try : 
            if not target_div:
                pass
            # Traverse up to the parent div
            par_div = target_div.find_parent('div')
            if not par_div:
                # print(f'pardiv1 Not found for bettype {bet_type}')
                pass
            parent_div = par_div.find_parent('div')
            if not parent_div:
                # print(f'pardiv2 Not found for bettype {bet_type}')
                pass
            parentFound=True
        except : 
            # print('Problem in getting parent div '+bet_type)
            parentFound=False
        if parentFound :    
            break
            
            

    for bet_type,normalized_bet_type,formatfunc in bet_types:
        result[normalized_bet_type] = {}
    # Find the div containing the 'Money Line – Match' text
        target_div = soup.find('span', string=lambda text: text and text == bet_type )

        try : 
            if not target_div:
                pass
            # Traverse up to the parent div
            par_div = target_div.find_parent('div')
            if not par_div:
                print(f'pardiv1 Not found for bettype {bet_type}')
                pass
            parent_div = par_div.find_parent('div')
            if not parent_div:
                print(f'pardiv2 Not found for bettype {bet_type}')
                pass
            parentFound=True
        except : 
            print('Problem in getting parent div '+bet_type)
            parentFound=False

        if parentFound:
            see_more_button = None
            see_more_div = parent_div.find('span', string=lambda text: text and 'See more' in text)
            if see_more_div : 
                see_more_button= see_more_div.find_parent('button')
            if see_more_button:
                try:
                    # Use an XPath relative to the unique section
                    button_xpath = f"//div[div[span[contains(text(), '{bet_type}')]]]//button[span[contains(text(), 'See more')]]"

                    button_element = driver.find_element(By.XPATH, button_xpath)
                    ActionChains(driver).move_to_element(button_element).click().perform()
                except Exception as e:
                    print(parent_div.prettify())
                    # print(f"Could not click 'See more' button: {e}")
            
                # Refresh the page source after interaction
                updated_html = driver.page_source
                soup = BeautifulSoup(updated_html, 'html.parser')
                target_div = soup.find('span', string=lambda text: text and bet_type in text)
                parent_div = target_div.find_parent('div').find_parent('div')


            # Find all buttons within that parent div
            buttons = parent_div.find_all('button')

            # Extract text from spans inside each button
            betlist=[]
            for button in buttons:
                spans = button.find_all("span")
                if len(spans) >= 2:
                    betlist.append((spans[0].get_text(strip=True), spans[1].get_text(strip=True)))
            result[normalized_bet_type]=formatfunc(betlist,team1,team2)
    return result

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
        if r[0]=="Draw":
            WLD["X"]=float(r[1])
    return WLD

def format_pinnacle_BTTS(res,team1,team2):#both team to score
    BTTS = {}
    for r in res:
        if r[0] == 'Yes': 
            BTTS['Yes']=float(r[1])
        elif r[0] == 'No':
            BTTS['No']=float(r[1])
    return BTTS

def format_pinnacle_OverUnder(res,team1,team2):
    OverUnders = {}
    for key, value in res:
        parts = key.split()
        if "Over" in parts:
            OverUnders[f"O_{parts[-1]}"] = float(value)
        elif "Under" in parts:
            OverUnders[f"U_{parts[-1]}"] = float(value)
    return OverUnders

def format_pinnacle_Handicap(res,team1,team2):
    HDC = {}
    t1="1"
    t2="2"
    if clean_string(team1)<=clean_string(team2):
        t1="2"
        t2="1"
    for i in range(0, len(res), 2):
        HDC[f"{t1}_{res[i][0]}"]=float(res[i][1])
        HDC[f"{t2}_{res[i+1][0]}"]=float(res[i+1][1])
    return HDC

