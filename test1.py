from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
from itertools import product
from itertools import combinations
import undetected_chromedriver as uc
import re
  # Headless mode to run without UI
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def get_matches_188():
    url = "https://sports.sportsbook-188.com/en-gb/sports/match/today/football/main_markets?coupon=102"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        page = browser.new_page()
        print("browser created")
        time.sleep(5)
        print("loading page")
        page.goto(url, timeout=600000)

        # Wait for key elements to load
        page.wait_for_selector("#app", timeout=30000)
        
        # Find the scrollable middle section
        scrollable_section = page.locator('.PageScrollWrapper')
        for i in range(5):
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            if soup.find_all('div', {'data-id': 'ParticipantAreaTeamNameWrapper'})==[]:
                time.sleep(2)
                scrollable_section.evaluate("element => element.scrollBy(0, -5500)")
        # Store unique team pairs
        teams_set = set()

        for _ in range(20):  # Keep scrolling until no new data appears
            # Extract HTML at this point
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract team names
            for wrapper in soup.find_all('div', {'data-id': 'ParticipantAreaTeamNameWrapper'}):
                team_names = [team.get_text(strip=True) for team in wrapper.find_all('div', {'data-id': 'ParticipantAreaTeamName'})]
                if len(team_names) == 2:
                    teams_set.add(tuple(team_names))  # Use set to avoid duplicates

            # Scroll inside the section
            scrollable_section.evaluate("element => element.scrollBy(0, 300)")
            time.sleep(0.2)  # Allow time for AJAX data to load


        # print(f"Total unique teams scraped: {len(teams_set)}")
        # print(teams_set)  # Print unique results

        browser.close()
        return teams_set
    
def get_all_bets_188(common,blank):
    r = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False,args=["--window-size=420,250"])  # Change to True if needed
        page = browser.new_page()
        time.sleep(5)
        for t188 in common:
            if t188!=-1:
                r.append(get_bets_188(page,t188))  # Replace with desired team names
            else : 
                r.append(blank) 
    return r
def get_all_bets_threader_188(queue_in,queue_out,blank):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False,args=["--window-size=420,250"])  # Change to True if needed
        page = browser.new_page()
        time.sleep(5)
        while True :
            to_get = queue_in.get()
            if to_get == 0:
                break 
            elif to_get == -1:
                queue_out.put(blank)
            else : 
                queue_out.put(get_bets_188(page,to_get))

def get_bets_188(page,target_teams):
    url = "https://sports.sportsbook-188.com/en-gb/sports/match/today/football/main_markets?coupon=102"
    team1,team2 = target_teams
    page.goto(url, timeout=600000)

    # Locate the scrollable section
    scrollable_section = page.locator('.PageScrollWrapper')
    for i in range(5):
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        if soup.find_all('div', {'data-id': 'ParticipantAreaTeamNameWrapper'})==[]:
            time.sleep(2)
            scrollable_section.evaluate("element => element.scrollBy(0, -5500)")
    time.sleep(0.5)
    # Scroll and search for the target team match
    found = False
    while not found:
        # Extract all displayed team matches
        match_containers = page.locator('[data-id="ParticipantAreaTeamNameWrapper"]').all()

        for container in match_containers:
            teams = container.locator('[data-id="ParticipantAreaTeamName"]').all()
            if len(teams) == 2:
 
                team_names = (teams[0].inner_text().strip(), teams[1].inner_text().strip())

                # Check if the current match is the target
                if team_names == target_teams:
                    print(f"Found match: {team_names}, clicking now...")
                    container.click()
                    found = True
                    break  # Exit loop after clicking

        if not found:
            # Scroll inside the middle section
            scrollable_section.evaluate("element => element.scrollBy(0, 300)")
            time.sleep(0.3)  # Allow AJAX data to load

    print("Click successful, closing browser.")
    bets = extract_bets(page,team1,team2)
    time.sleep(0.1)

    return bets

# Example usage:
def extract_odds_text(odds_box):
    return [h4.get_text(strip=True) for h4 in odds_box.find_all("h4")]

def extract_bets(page,team1,team2):
    time.sleep(1)
    bets={}
    scrollable_section = page.locator('.PageScrollWrapper')
    bet_types = [("Goals: Over / Under","OU",format_188bet_OverUnder),("1 X 2","WLD",format_188bet_1X2),("Both Teams To Score","BTTS",format_188bet_BTTS)]#"Half Time / Full Time ",,("Half Time / Full Time","HF_FT",format_188bet_HalfTime_FullTime)
    for bet_type,norm_bet_type,formatter in bet_types:
        # Scroll and search for the target team match
        scrollable_section.evaluate("element => element.scrollBy(0, -3800)")
        found = False
        iterations = 0
        while iterations < 10:
            scrollable_section.evaluate("element => element.scrollBy(0, -3800)")
            time.sleep(0.3)
            for _ in range(10):
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")
                target_div = None
                element = soup.find('h3', string=bet_type)
                if element:
                    target_div= element.find_parent('div').find_parent('div').find_parent('div').find_parent('div').find_parent('div')
                    found = True
            
                if not found:
                    iterations+=1
                    # Scroll inside the middle section
                    scrollable_section.evaluate("element => element.scrollBy(0, 400)")
                    time.sleep(0.4)  # Allow AJAX data to load
                else : 
                    iterations = 10
                    break
        if found :
            list_of_ods = []
            odds_boxes = target_div.find_all("div", {"data-crt-odds-box": "true"})
            for box in odds_boxes:
                list_of_ods.append(extract_odds_text(box))
            bets[norm_bet_type]=formatter(list_of_ods,team1,team2)
    return bets
        
def clean_string(s):
    # Remove unwanted patterns
    s= s.lower()
    s = re.sub(r'afc|ac|fc|as|vfl|vfb|\s|fsv|tsg|rb|-|\b\d+\.\b|\d+| i | ii ', '', s)
    # Convert to lowercase and remove spaces
    return s.replace(" ", "")

def format_188bet_1X2(res,team1,team2):
    WLD = {}
    if clean_string(team1)>clean_string(team2):
        for r in [0,1,2]:
            if len(res)>=r+1:
                WLD[res[r][0]]=float(res[r][1])
        for r in [3,4,5]:
            if len(res)>=r+1:
                WLD["1st_Half_"+res[r][0]]=float(res[r][1])
    else : 
        for r in [0,1,2]:
            if len(res)>=r+1:
                if r==0:
                    WLD["2"]=float(res[r][1])
                if r==1:
                    WLD["X"]=float(res[r][1])
                if r==2:
                    WLD["1"]=float(res[r][1])                

        for r in [3,4,5]:
            if len(res)>=r+1:
                if r==3:
                    WLD["1st_Half_2"]=float(res[r][1])
                if r==4:
                    WLD["1st_Half_X"]=float(res[r][1])
                if r==5:
                    WLD["1st_Half_1"]=float(res[r][1])   
    return WLD

def format_188bet_BTTS(res,team1,team2):#both team to score
    BTTS = {}
    for r in [0,1]:
        if len(res) >= 2:
            BTTS[res[r][0]]=float(res[r][1])
    for r in [2,3]:
        if len(res) >= 4:
            BTTS["1st_Half_"+res[r][0]]=float(res[r][1])
    return BTTS

def format_188bet_OverUnder(res,team1,team2):
    OverUnders = {}
    for r in res:
        if r != []:
            OverUnders[f"{r[0]}_{r[1]}"]=float(r[2])+1
    return OverUnders

def format_188bet_HalfTime_FullTime(res,team1,team2):
    HTFT = {}
    team={"Draw":"0",team1:"1",team2:"2"}
    for r in res:
        bet=[team[s] for s in r[0].split(" / ")]
        HTFT[bet[0]+bet[1]]=float(r[1])
    return HTFT


