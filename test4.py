from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import re
# Set up headless Chrome


# Create a new Chrome session

def get_matches_ivi():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--window-size=700,500")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--ssl-version-max=tls1.2")
    driver = webdriver.Chrome(options=chrome_options)
    time.sleep(5)
    try:
        # Navigate to the URL
        url = "https://ivibet.com/prematch/football"
        driver.get(url)
        time.sleep(4)  # Adjust the sleep time as needed
        for i in range(10):  # Scroll 3 times, adjust as needed
            events_data = []
            driver.execute_script("window.scrollBy(0, 200);")  # Scroll down 500 pixels 
            time.sleep(1)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            # Find all <a> tags with data-test="eventLink"
            event_links = soup.find_all("a", {"data-test": "eventLink"})
            if event_links != []:
                # List to store tuples
                time.sleep(1)
                soup = BeautifulSoup(driver.page_source, "html.parser")
                # Find all <a> tags with data-test="eventLink"
                event_links = soup.find_all("a", {"data-test": "eventLink"})
                
                found = True
                for event in event_links:
                    # Get the href
                    href = event.get("href", "")
                    
                    # Find the div that contains the team names.
                    # According to your snippet, team names are inside <div data-test="teamSeoTitles">, then within <span>
                    team_container = event.find("div", {"data-test": "teamSeoTitles"})
                    if team_container:
                        # The team names are in <span> tags, one for each team.
                        spans = team_container.find_all("span")
                        if len(spans) >= 2:
                            team1 = spans[0].get_text(strip=True)
                            team2 = spans[1].get_text(strip=True)
                            events_data.append((team1, team2,href))
                        else:
                            # In case there are not two spans, add a placeholder
                            # events_data.append((None, None, href))
                            found = False
                    else:
                        # events_data.append((None, None, href))
                        found = False
                if found :
                    break
                # Print the list of tuples
                # for event_tuple in events_data:
                #     print(event_tuple)
            
    except Exception as e:
        print("An error occurred:", e)
    finally:
        driver.quit()
    return events_data

def get_all_bets_Ivi(common,blank):
    r = []
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    time.sleep(5)
    for tIvi in common:
        if tIvi!=-1:
            r.append(get_bets_ivi(driver,tIvi))  # Replace with desired team names
        else : 
            r.append(blank) 
    return r

def get_bets_ivi(driver,match):
    team1,team2,match_url = match
    url = "https://ivibet.com"+match_url
    driver.get(url)
    bet_dict = {}
    for _ in range(10):
        soup = BeautifulSoup(driver.page_source, "html.parser")
        time.sleep(1)
        driver.execute_script("window.scrollBy(0, 50);")
        if soup.find_all("div",{'data-test': 'market-countainer'}) != []:
            print("here")
            break
    soup = BeautifulSoup(driver.page_source, "html.parser")
    all_bets = {}
    for bet_market in soup.find_all("div",{'data-test': 'market-countainer'}):
        market_header = bet_market.find("div", {'data-test': 'sport-event-table-market-header'})
        # Find the span within that div and get its text
        if market_header:
            bet_type = market_header.find("span").get_text(strip=True) if market_header.find("span") else None
            bets_divs = bet_market.find_all("div", {'data-test': 'sport-event-table-additional-market'})
            bets = []
            
            for div in bets_divs:
                span_texts = tuple(span.get_text(strip=True) for span in div.find_all("span"))
                bets.append(span_texts)
            all_bets[bet_type]=bets
    # print(soup.find_all("div",{'data-test': 'market-countainer'}))
    bet_types = [('Total',"OU",format_ivi_OverUnder),("1x2","WLD",format_ivi_1X2),("Both teams to score","BTTS",format_ivi_BTTS),("Handicap","Handicap",format_ivi_Handicap)]

    for key,bet_name,formatter in bet_types :
        if key in all_bets.keys():
            bet_dict[bet_name]= formatter(all_bets[key],team1,team2)
        else :
            bet_dict[bet_name]={}
    return bet_dict
    
def clean_string(s):
    return re.sub(r'AC|FC|AS|\s|-', '', s).lower().replace(" ", "")

def format_ivi_1X2(res,team1,team2):
    WLD = {}
    if clean_string(team1)<=clean_string(team2):
        tt=team1
        team1=team2
        team2=tt
    for r in res:
        value = max([float(x) for x in r if isinstance(x, str) and x.replace('.', '', 1).isdigit()])
        if r[0]==team1:
            WLD["1"]=value
        if r[0]==team2:
            WLD["2"]=value
        if r[0]=="draw":
            WLD["X"]=value
    return WLD

def format_ivi_BTTS(res,team1,team2):#both team to score
    BTTS = {}
    for r in res:
        value = max([float(x) for x in r if isinstance(x, str) and x.replace('.', '', 1).isdigit()])
        if r[0] == 'yes': 
            BTTS['Yes']=value
        elif r[0] == 'no':
            BTTS['No']=value
    return BTTS

def format_ivi_OverUnder(res,team1,team2):
    OverUnders = {}
    for r in res:
        value = max([float(x) for x in r if isinstance(x, str) and x.replace('.', '', 1).isdigit()])
        parts = r[0].split()
        if "over" in parts:
            OverUnders[f"O_{parts[-1]}"] = value
        elif "under" in parts:
            OverUnders[f"U_{parts[-1]}"] = value
    return OverUnders

def format_ivi_Handicap(res,team1,team2):
    HDC = {}
    if clean_string(team1)<=clean_string(team2):
        tt=team1
        team1=team2
        team2=tt
    for r in res:
        parts = r[0].split()
        handicap = parts.pop(-1).strip("()")
        team = clean_string(" ".join(parts))
        if team==clean_string(team1):
            HDC[f"1_{handicap}"]=float(r[1])
        if team==clean_string(team2):
            HDC[f"2_{handicap}"]=float(r[1])

    return HDC

# print(get_bets_ivi(driver,('Club Brugge', 'Aston Villa', '/prematch/football/1008006-uefa-champions-league/5529868-club-brugge-aston-villa'))) #get_matches_ivi()[0]))
# get_bets_ivi(driver,('Liverpool FC', 'Southampton FC', '/prematch/football/1008013-premier-league/5546294-liverpool-fc-southampton-fc'))
    