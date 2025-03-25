from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import re
# Set up headless Chrome
import json

# Create a new Chrome session
#
# https://megapari.com/service-api/LineFeed/GetGameZip?id=250242734&lng=en&isSubGames=true&GroupEvents=true&countevents=250&grMode=4&partner=192&topGroups=&country=83&marketType=1
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=3")

    chrome_options.add_argument("--window-size=700,500")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ssl-version-max=tls1.2")
    driver = webdriver.Chrome(options=chrome_options)
    time.sleep(5)
    return driver

def get_matches_mega(driver = setup_driver(),selfdriver = True):
    try:
        # Navigate to the URL
        url = "https://megapari.com/en/line/football"
        driver.get(url)
        time.sleep(6)  # Adjust the sleep time as needed
        for i in range(6):  # Scroll 3 times, adjust as needed
            driver.execute_script("window.scrollBy(0, 500);")  # Scroll down 500 pixels 
            time.sleep(1)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            # Find all <a> tags with data-test="eventLink"
            event_links = soup.find_all("a", {"class": "dashboard-game-block-link"})
            if event_links != []:
                print('here')
                break
        # List to store tuples
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # Find all <a> tags with data-test="eventLink"
        event_links = soup.find_all("a", {"class": "dashboard-game-block-link"})
        events_data = []
        
        for event in event_links:
            # Get the href
            href = event.get("href", "")
            
            # Find the div that contains the team names.
            # According to your snippet, team names are inside <div data-test="teamSeoTitles">, then within <span>
            team_containers = event.findAll("span", {"class": "dashboard-game-team-info__name"})
            if team_containers != []:
                if len(team_containers) >= 2:
                    team1 = team_containers[0].get_text(strip=True)
                    team2 = team_containers[1].get_text(strip=True)
                    events_data.append((team1, team2,href))
                else:
                    # In case there are not two spans, add a placeholder
                    events_data.append((None, None, href))
            else:
                events_data.append((None, None, href))
        
            
    except Exception as e:
        print("An error occurred:", e)
    finally:
        if selfdriver:
            driver.quit()
    return events_data
# get_matches_mega()

def get_all_bets_Mega(common,blank):
    r = []
    driver= setup_driver()
    for tMega in common:
        if tMega!=-1:
            r.append(get_bets_mega(driver,tMega))  # Replace with desired team names
        else : 
            r.append(blank) 
    return r
def get_all_bets_threader_Mega(queue_in,queue_out,blank):
    driver= setup_driver()
    while True :
        to_get = queue_in.get()
        if to_get == 0:
            driver.quit()
            break 
        elif to_get == -1:
            queue_out.put(blank)
        else : 
            queue_out.put(get_bets_mega(driver,to_get))
            
def get_bets_mega(driver,match):
    team1,team2,match_url = match
    
    id_match = match_url.split('/')[-1].split('-')[0]
    url = f'https://megapari.com/service-api/LineFeed/GetGameZip?id={id_match}&lng=en&isSubGames=true&GroupEvents=true&countevents=250&grMode=4&partner=192&topGroups=&country=83&marketType=1'
    driver.get(url)
    # print(url)
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    json_text = soup.find('pre').text
    response = json.loads(json_text)

    try :
        allbet = response['Value']['GE']
        found = True
    except : 
        found = False
        print(url)
        print("https://megapari.com"+match_url)    
        all_match = get_matches_mega(driver=driver,selfdriver=False)
        for t1,t2,m_url in all_match:
            if clean_string(t1) == clean_string(team1) and clean_string(t2) == clean_string(team2):
                id_match = m_url.split('/')[-1].split('-')[0]
                url = f'https://megapari.com/service-api/LineFeed/GetGameZip?id={id_match}&lng=en&isSubGames=true&GroupEvents=true&countevents=250&grMode=4&partner=192&topGroups=&country=83&marketType=1'
                driver.get(url)
                print(f'New url : {url}')
                time.sleep(1)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                json_text = soup.find('pre').text
                response = json.loads(json_text)
                allbet = response['Value']['GE']
                found= True
    bet_types = [('Total',"OU",format_mega_OverUnder),("1x2","WLD",format_mega_1X2),("Both teams to score","BTTS",format_mega_BTTS)]
    all_bets={}
    if found :
        
        if 'P' in allbet[3]['E'][0][0].keys():
            offset = 0
        else: 
            offset = 1
        all_bets["1x2"]=[bet[0]['C'] for bet in allbet[0]['E']]
        all_bets["Both teams to score"]=[('yes',allbet[3]['E'][0][0]['C']),('no',allbet[2+offset]['E'][1][0]['C'])]
        all_bets["Total"]=[(bet['T'],bet['P'],bet['C']) for bet in allbet[3+offset]['E'][0]+allbet[3+offset]['E'][1]] #Colonne,Nbbut,Cote
    else : 
        print('NOT FOUND')
    bet_dict = {}
        
    for key,bet_name,formatter in bet_types :
        if key in all_bets.keys():
            bet_dict[bet_name]= formatter(all_bets[key],team1,team2)
        else :
            bet_dict[bet_name]={}
    return bet_dict
    
def clean_string(s):
    # Remove unwanted patterns
    s= s.lower()
    s = re.sub(r'afc|ac|fc|as|vfl|vfb|\s|fsv|tsg|rb|-|\b\d+\.\b|\d+| i | ii ', '', s)
    # Convert to lowercase and remove spaces
    return s.replace(" ", "")

def format_mega_1X2(res,team1,team2):
    WLD = {}
    if clean_string(team1)<=clean_string(team2):
        WLD["1"]=res[2]
        WLD["2"]=res[0]
    else:
        WLD["1"]=res[0]
        WLD["2"]=res[2]
    WLD["X"]=res[1]
    return WLD

def format_mega_BTTS(res,team1,team2):#both team to score
    BTTS = {}
    for r in res:
        value = float(r[1])
        if r[0] == 'yes': 
            BTTS['Yes']=value
        elif r[0] == 'no':
            BTTS['No']=value
    return BTTS

def format_mega_OverUnder(res,team1,team2):
    OverUnders = {}
    for r in res:
        value = float(r[2])
        parts = r[0]
        if 9 == parts:
            OverUnders[f"O_{r[1]}"] = value
        elif 10 == parts:
            OverUnders[f"U_{r[1]}"] = value
    return OverUnders
