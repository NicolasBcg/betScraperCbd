import requests
from bs4 import BeautifulSoup
import time
import undetected_chromedriver as uc
import re
  # Headless mode to run without UI
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def setup_driver():
    """Set up a Selenium WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    time.sleep(5)  # Ensure we don't trigger rate limits
    return driver

def get_matches_1xbet():
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")

    driver = uc.Chrome(options=chrome_options)
    time.sleep(5)
    driver.get("https://1xbet.com/en/line/football")

    time.sleep(1)

    # Check if the request was successful
    matches = []
    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find all scoreboard layouts
        for event in soup.find_all(class_="c-events-scoreboard__layout"):
            # Extract href from event name
            name_tag = event.find(class_="c-events__name")
            href = name_tag["href"] if name_tag and "href" in name_tag.attrs else None

            # Extract team names
            team_tags = event.find_all("div", class_="c-events__team")
            teams = [team.get_text(strip=True) for team in team_tags]

            if href and len(teams) == 2:
                matches.append((teams[0], teams[1],href))        
    except:
        print(f"Not properly closed")
    try: 
        driver.quit()
    except:
        print(f"Not properly closed")
        return matches
    return matches


def get_all_bets_threader_1xbet(queue_in,queue_out,blank):
    driver= setup_driver()
    while True :
        to_get = queue_in.get()
        if to_get == 0:
            driver.quit()
            break 
        elif to_get == -1:
            queue_out.put(blank)
        else : 
            queue_out.put(get_bets_1xbet(driver,to_get,blank))



def get_all_bets_1xbet(common,blank):
    s1x = []
    driver=setup_driver()
    for t1xbet in common:
        if t1xbet!=-1:
            s1x.append(get_bets_1xbet(driver,t1xbet,blank))  # Replace with desired team names
        else : 
            s1x.append(blank)
    return s1x

def get_bets_1xbet(driver,match,blank={}):
    team1,team2,match_url = match

    url = "https://1xbet.com"+match_url
    try:
        driver.get(url)
    except:
        return blank
    time.sleep(1)
    bet_dict = {}
    soup = BeautifulSoup(driver.page_source, "html.parser")
    for bet_group in soup.find_all("div", class_="bet_group"):
        # Find the bet title
        title_span = bet_group.find("span", class_="bet-title-label")
        
        if not title_span:
            continue  # Skip if title not found
        
        title = title_span.get_text(strip=True)
        
        bets = []
        for bet_inner in bet_group.find_all("div", class_="bet-inner"):
            bet_type = bet_inner.find("span", class_="bet_type")
            koeff_label = bet_inner.find("span", class_="koeff__label")
            
            if bet_type and koeff_label:
                bets.append((bet_type.get_text(strip=True), koeff_label.get_text(strip=True)))
        
        bet_dict[title] = bets
    bets={}
    if "Asian Handicap" in bet_dict.keys():
        bet_dict["Handicap"] = bet_dict["Handicap"]+bet_dict["Asian Handicap"]
    bet_types = [('Total',"OU",format_1xbet_OverUnder),("1x2","WLD",format_1xbet_1X2),("Both Teams To Score","BTTS",format_1xbet_BTTS),("Handicap","Handicap",format_1xbet_Handicap)]
    # Print the extracted dictionary
    for key,bet_name,formatter in bet_types :
        
        if key in bet_dict.keys():
            bets[bet_name]= formatter(bet_dict[key],team1,team2)

    return bets


def clean_string(s):
    return re.sub(r'AC|FC|AS|\s|-', '', s).lower().replace(" ", "")
def format_1xbet_1X2(res,team1,team2):
    WLD = {}
    if clean_string(team1)<=clean_string(team2):
        tt=team1
        team1=team2
        team2=tt
    for r in res:

        if r[0]==team1:
            WLD["1"]=float(r[1])
        if r[0]==team2:
            WLD["2"]=float(r[1])
        if r[0]=="Draw":
            WLD["X"]=float(r[1])
    return WLD

def format_1xbet_BTTS(res,team1,team2):#both team to score
    BTTS = {}
    for r in res:
        if r[0] == 'Both Teams To Score - Yes': 
            BTTS['Yes']=float(r[1])
        elif r[0] == 'Both Teams To Score - No':
            BTTS['No']=float(r[1])
    return BTTS

def format_1xbet_OverUnder(res,team1,team2):
    OverUnders = {}
    for key, value in res:
        parts = key.split()
        if "Over" in parts:
            OverUnders[f"O_{parts[-1]}"] = float(value)
        elif "Under" in parts:
            OverUnders[f"U_{parts[-1]}"] = float(value)
    return OverUnders

def format_1xbet_Handicap(res,team1,team2):
    HDC = {}
    if clean_string(team1)<=clean_string(team2):
        tt=team1
        team1=team2
        team2=tt
    for r in res:
        parts = r[0].split()
        parts.pop(0)
        handicap = parts.pop(-1).strip("()")
        team = clean_string(" ".join(parts))
        if team==clean_string(team1):
            HDC[f"1_{handicap}"]=float(r[1])
        if team==clean_string(team2):
            HDC[f"2_{handicap}"]=float(r[1])

    return HDC
