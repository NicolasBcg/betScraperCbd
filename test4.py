from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import re
import threading
from queue import Queue
# Set up headless Chrome

def setup_driver():
    """Set up a Selenium WebDriver instance."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(15)
    time.sleep(5)  # Ensure we don't trigger rate limits
    return driver
# Create a new Chrome session

def process_league(driver, link_div):
    """Fetch event data from a single league page using a shared driver."""
    league_url = "https://ivibet.com" + link_div
    driver.get(league_url)
    time.sleep(0.5)
    
    events_data = []
    
    for _ in range(10):  # Scroll multiple times to load matches
        time.sleep(0.5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        event_links = soup.find_all("a", {"data-test": "eventLink"})
        
        if event_links:
            for event in event_links:
                href = event.get("href", "")
                team_container = event.find("div", {"data-test": "teamSeoTitles"})
                
                if team_container:
                    spans = team_container.find_all("span")
                    if len(spans) >= 2:
                        team1 = spans[0].get_text(strip=True)
                        team2 = spans[1].get_text(strip=True)
                        events_data.append((team1, team2, href))
            
            break  # Stop scrolling if data is found

    return events_data

def worker(queue, results):
    """Thread worker function to process leagues using a shared driver."""
    driver = setup_driver()
    while not queue.empty():
        link_div = queue.get()
        if link_div is None:
            driver.quit()
            break  # Stop if we get a termination signal

        try:
            events = process_league(driver, link_div)
            results.extend(events)  # Append results safely
        except Exception as e:
            print(f"Error processing league: {e}")
        finally:
            queue.task_done()  # Mark task as completed
def get_matches_ivi():
    """Main function to get matches using a limited WebDriver pool."""
    driver = setup_driver()  # Single driver for main page

    # Load the main page
    driver.get("https://ivibet.com/prematch/football/leagues")
    time.sleep(2)
    
    # Extract championship links
    championship_Links = []
    for _ in range(10):
        soup = BeautifulSoup(driver.page_source, "html.parser")
        championship_Links = [a["href"] for a in soup.select('div[data-test="sportPageWrapper"] a') if "href" in a.attrs]

        # championship_Links = soup.find_all(class_=re.compile(r'leagues-list_name'))
        if championship_Links:
            break
        time.sleep(1)

    driver.quit()  # Close the initial driver

    if not championship_Links:
        print("IVI NOT FOUND")
        return []

    # Create a queue and populate it with league links
    queue = Queue()
    print('links')
    print(len(championship_Links))
    for link_div in championship_Links:
        queue.put(link_div)


    results = []
    threads = []

    # Start worker threads, each with a driver
    for _ in range(3):
        thread = threading.Thread(target=worker, args=(queue, results))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()


    return results
if __name__ == "__main__":
    start = time.time()
    for m in get_matches_ivi():
        print(m)
    print(time.time()-start)




def get_all_bets_Ivi(common,blank):
    r = []
    driver = setup_driver()
    for tIvi in common:
        if tIvi!=-1:
            r.append(get_bets_ivi(driver,tIvi))  # Replace with desired team names
        else : 
            r.append(blank) 
    return r

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
            queue_out.put(get_bets_ivi(driver,to_get))

def get_bets_ivi(driver,match):
    team1,team2,match_url = match
    url = "https://ivibet.com"+match_url
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
                span_texts = tuple(span.get_text(strip=True) for span in div.find_all("span"))
                bets.append(span_texts)
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
        try:
            value = max([float(x) for x in r if isinstance(x, str) and x.replace('.', '', 1).isdigit()])
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
            value = max([float(x) for x in r if isinstance(x, str) and x.replace('.', '', 1).isdigit()])
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
            value = max([float(x) for x in r if isinstance(x, str) and x.replace('.', '', 1).isdigit()])
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
