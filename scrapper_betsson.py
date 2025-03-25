from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
# Set up headless Chrome
import json

# Create a new Chrome session
#

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

def get_matches_betsson(driver = setup_driver()):
    """Main function to get matches using a limited WebDriver pool."""
      # Single driver for main page

    # Load the main page
    driver.get("https://www.betsson.com/en/sportsbook/football?tab=liveAndUpcoming")
    time.sleep(3)

    try:
        for div in ["Upcoming Today","Tomorrow"]:
            # Wait until the span with the text "Upcoming Today" is present
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//span[text()='{div}']"))
            )
            
            # Click the element once it appears
            element.click()

        # Find all elements that represent the "Show All ..." buttons
        show_all_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//span[contains(text(), 'Show all')]"))
        )
        
        # Iterate through each "Show All" button and click it
        for button in show_all_buttons:
            button.click()
            print("Clicked on 'Show All' button!")
        time.sleep(0.5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        all_events = soup.findAll('a', {'test-id': 'event-row.link'})
        match_links = [(a["href"],a) for a in all_events if "href" in a.attrs]
        match_links_clean = [(url,a) for url,a in match_links if '/en/sportsbook/football/efootball/' not in url]
        all_events=[]
        for link,div_match in match_links_clean:
            participant_divs = div_match.find_all('div', {'test-id': 'event-info.participant'})
            # Extract text from the span inside each div
            participants = [div.find('span').text for div in participant_divs]
            all_events.append((participants[0],participants[1],link))
        if all_events:
            driver.quit()
        else :
            print("Pinnacle Match not found : retrying ...")
            return get_matches_betsson(driver)
            
    except Exception as e:
        print("Error:", e)
        return get_matches_betsson(driver)
      # Close the initial driver
    return all_events

def get_odds(driver,url):
    driver.get(url)
    
    market_countainers = []
    for _ in range(10):
        time.sleep(0.5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        market_countainers = soup.find_all(True,{'test-id': 'event.market-group'})
        if market_countainers != []:
            found = False
            all_bets = {}
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            market_countainers = soup.find_all(True,{'test-id': 'event.market-group'})
            for bet_market in market_countainers:
                market_header = bet_market.find("div", class_=re.compile(r"market-group-header"))
                # Find the span within that div and get its text
                if market_header:
                    bet_type = market_header.find("span").get_text(strip=True) if market_header.find("span") else None
                    bets_divs = bet_market.find_all(True, {'test-id': 'selection.base'})
                    bets = []

                    for div in bets_divs:
                        texts=[span.get_text(strip=True) for span in div.find_all("span")]
                        span_texts = tuple(texts)
                        bets.append(span_texts)
                        if len(texts)>=2:
                            found = True
                    all_bets[bet_type]=bets
            if found : 
                return all_bets
            else :
                return get_odds(driver,url)
    return get_odds(driver,url)

def get_bets_betsson(driver,match):
    team1,team2,match_url = match
    url = "https://www.betsson.com"+match_url
    all_bets = get_odds(driver,url)
    
    bet_types = [('Total Goals',"OU",format_betsson_OverUnder),("Match Result","WLD",format_betsson_1X2),("Both teams to score","BTTS",format_betsson_BTTS)]
    bet_dict = {}
    for key,bet_name,formatter in bet_types :
        if key in all_bets.keys():
            bet_dict[bet_name]= formatter(all_bets[key],team1,team2)
        else :
            bet_dict[bet_name]={}
    print(bet_dict)
    return bet_dict
    
def clean_string(s):
    # Remove unwanted patterns
    s= s.lower()
    s = re.sub(r'afc|ac|fc|as|vfl|vfb|\s|fsv|tsg|rb|-|\b\d+\.\b|\d+| i | ii ', '', s)
    # Convert to lowercase and remove spaces
    return s.replace(" ", "")


def format_betsson_1X2(res,team1,team2):
    WLD = {}
    if clean_string(team1)<=clean_string(team2):
        tt=team1
        team1=team2
        team2=tt
    for r in res:
        try:
            value = max([float(x) for x in r if isinstance(x, str) and x.replace('.', '', 1).isdigit()])
            if r[0]==team1:
                WLD["1"]=value
            if r[0]==team2:
                WLD["2"]=value
            if r[0]=="Draw":
                WLD["X"]=value
        except : 
            print(f'ERROR BETSSON 1X2 VALUE {team1},{team2}  : {r} ')
    return WLD

def format_betsson_BTTS(res,team1,team2):#both team to score
    BTTS = {}
    for r in res:
        try : 
            value = max([float(x) for x in r if isinstance(x, str) and x.replace('.', '', 1).isdigit()])
            if r[0] == 'Yes': 
                BTTS['Yes']=value
            elif r[0] == 'No':
                BTTS['No']=value
        except : 
            print(f'ERROR BETSSON BTTS VALUE {team1},{team2}  : {r} ')
    return BTTS

def format_betsson_OverUnder(res,team1,team2):
    OverUnders = {}
    for r in res:
        try: 
            value = max([float(x) for x in r if isinstance(x, str) and x.replace('.', '', 1).isdigit()])
            parts = r[0].split()
            if "Over" in parts:
                OverUnders[f"O_{parts[-1]}"] = value
            elif "Under" in parts:
                OverUnders[f"U_{parts[-1]}"] = value
        except : 
            print(f'ERROR BETSSON OU VALUE {team1},{team2}  : {r} ')
    return OverUnders

def get_all_bets_threader_Betsson(queue_in,queue_out,blank):
    driver= setup_driver()
    while True :
        to_get = queue_in.get()
        if to_get == 0:
            driver.quit()
            break 
        elif to_get == -1:
            queue_out.put(blank)
        else : 
            queue_out.put(get_bets_betsson(driver,to_get))