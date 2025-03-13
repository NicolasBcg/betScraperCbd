from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup
import time
import re

# Set up Selenium with headless Chrome

def get_matches_pinnacle():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    time.sleep(5)
    url = "https://www.pinnacle.bet/en/soccer/matchups/highlights/"
    driver.get(url)

    # Wait for the dynamic content to load (adjust time as needed or use explicit waits)
    time.sleep(10)
    for _ in range(8):
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        matches = []

        for a in soup.find_all("a", href=True):
            flex_div = a.find("div", class_=lambda x: x and "flex-row" in x)
            if not flex_div:
                continue

            main_href = a["href"].rstrip("/") 

            spans = flex_div.find_all("span", class_="ellipsis")
            if len(spans) < 2:
                continue

            team1 = preprocess_team_names(spans[0].get_text(strip=True))
            team2 = preprocess_team_names(spans[1].get_text(strip=True))
            matches.append(( team1, team2,main_href))
        if matches!=[]: 
            break
        time.sleep(3)

    # for match in matches:
    #     print(match)
    driver.quit()
    return list(set(matches))

def preprocess_team_names(name):
    return re.sub(r'\s*\(.*?\)', '', name).lower()

# get_matches_pinnacle()

def clean_string(s):
    return re.sub(r'AC|FC|AS|\s|-', '', s).lower().replace(" ", "")


def get_all_bets_Pinnacle(common,blank):
    r = []
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    time.sleep(5)
    for tPinnacle in common:
        if tPinnacle!=-1:
            r.append(get_bets_pinnacle(driver,tPinnacle))  # Replace with desired team names
        else : 
            r.append(blank) 
    return r

def get_bets_pinnacle(driver, match):
    team1,team2,match_url = match
    base_url = "https://www.pinnacle.bet"+match_url
    # ,("Both Teams To Score","BTTS",format_pinnacle_BTTS)
    url = base_url+'/#period:0'
    bet_types = [('Total – Match',"OU",format_pinnacle_OverUnder),('Money Line – Match',"WLD",format_pinnacle_1X2),('Handicap – Match',"Handicap",format_pinnacle_Handicap)]
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
            html = driver.page_source
            # print(html)
            soup = BeautifulSoup(html, "html.parser")    
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
        HDC[f"1_{res[i][0]}"]=float(res[i][1])
        HDC[f"2_{res[i][0]}"]=float(res[i][1])
    return HDC



#print(get_odds(driver_pinnacle,('/en/soccer/england-premier-league/crystal-palace-vs-aston-villa/1604645964', 'Crystal Palace (Match)', 'Aston Villa (Match)')))

