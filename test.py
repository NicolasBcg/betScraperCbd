from playwright.sync_api import sync_playwright
import time
from itertools import combinations
import undetected_chromedriver as uc
import threading
from queue import Queue
  # Headless mode to run without UI
import re
from test1 import *
from test2 import *
from test3 import *
from test4 import *
from test5 import *



def treat_BTTS(sites):
    found=[]
    print(sites)
    for bet in ["","1st_Half_"]:
        for site1,s1name in sites:
            for site2,s2name in sites:
                if s2name!=s1name:
                    try :
                        ratio = 1/site1[bet+"Yes"]+1/site2[bet+"No"]
                        if ratio<= 1.015:
                            print(f"YN ratio {ratio}")
                        if ratio<= 0.997:
                            found.append((f"{s1name}_Yes_{s2name}_No_{bet}",ratio))
                    except: 
                        pass
    return found
def treat_WLD(sites):
    found=[]
    print(sites)
    for bet in ["","1st_Half_"]:
        for site1,s1name in sites:
            for site2,s2name in sites: 
                for site3,s3name in sites:
                    if not (s2name==s1name and s2name==s3name):
                        try : 
                            ratio = 1/site1[bet+"1"]+1/site2[bet+"X"]+1/site3[bet+"2"]
                            if ratio<= 1.015:
                                print(f"WLD ratio {s1name}_1_{s2name}_X_{s3name}_2_{bet} {ratio}")
                            if ratio<= 0.997:
                                found.append((f"{s1name}_1_{s2name}_X_{s3name}_2_{bet}",ratio))
                        except:
                            # print(f"{s1name}_1_{s2name}_X_{s3name}_2_{bet}")
                            pass
    return list(set(found))

def treat_Handicap_WLD(sitesHandicap,sitesWLD):
    found = []
    for oddsHandicap,sname1 in sitesHandicap:
        if oddsHandicap!={}:
            print(f'{sname1} : {oddsHandicap}')
            for site2,sname2 in sitesWLD: 
                for site3,sname3 in sitesWLD: 
                    for hdTeam,winTeam in [("1_0","2"),("2_0","1")]:
                        if not (sname2==sname1 and sname2==sname3):
                            try:
                                o1 = oddsHandicap[hdTeam]
                                draw = site2["X"]
                                w2 = site3[winTeam]
                                try : 
                                    ratio = (1/o1)+ (o1-1)/(o1*draw)+(1/w2)
                                    if ratio<= 1.015:
                                        print(f"Handi {hdTeam} WLD ratio {sname1}_1_{o1}handi0_{sname2}_X_{draw}_{sname3}_2_{w2} {ratio}")
                                    if ratio<= 0.995:
                                        found.append((f"Handi WLD {sname1}_1_{sname2}_X_{sname3}_2",ratio))
                                except :
                                    pass
                            except:
                                pass

                    for hdTeam,winTeam in [("1_+0.25","2"),("2_+0.25","1")]:
                        if not (sname2==sname1 and sname2==sname3):
                            try:
                                o1 = oddsHandicap[hdTeam]
                                draw = site2["X"]
                                w2 = site3[winTeam]
                                try : 
                                    ratio = (1/o1)+ (1/(2*draw))+(1/w2)
                                    if ratio<= 1.015:
                                        print(f"Handi {hdTeam} WLD ratio {sname1}_1_{o1}handi0_{sname2}_X_{draw}_{sname3}_2_{w2} {ratio}")
                                    if ratio<= 0.995:
                                        found.append((f"{sname1}_1_{sname2}_X_{sname3}_2",ratio))
                                except :
                                    pass
                            except:
                                pass
                    for hdTeam,winTeam in [("1_-0.25","2"),("2_-0.25","1")]:
                        if not (sname2==sname1 and sname2==sname3):
                            try:
                                o1 = oddsHandicap[hdTeam]
                                draw = site2["X"]
                                w2 = site3[winTeam]
                                try : 
                                    ratio = (1/o1)+ (1-(1/(2*o1)))/(draw)+(1/w2)
                                    if ratio<= 1.015:
                                        print(f"Handi {hdTeam} WLD ratio {sname1}_1_{o1}handi0_{sname2}_X_{draw}_{sname3}_2_{w2} {ratio}")
                                    if ratio<= 0.995:
                                        found.append((f"{sname1}_1_{sname2}_X_{sname3}_2",ratio))
                                except :
                                    pass
                            except:
                                pass

    return found

def treat_OverUnder(sites):
    found=[]
    print(sites)
    for site1,s1name in sites:
        for site2,s2name in sites:
            if s2name!=s1name:
                for i in ["0.5","1.5","2.5","3.5","4.5"]:
                    try : 
                        ratio = 1/site1["O_"+i]+1/site2["U_"+i]
                        if ratio<= 1.01:
                            print(f"OU {i} ratio {ratio}")
                        if ratio<= 0.995:
                            found.append((f"{s1name}_O_{s2name}_U_{i}",ratio))
                    except : 
                        pass
                for i in ["0.5","1","1.5","2","2.5"]:
                    try : 
                        ratio = 1/site1["1_+"+i]+1/site2["2_-"+i]
                        if ratio<= 1.015:
                            print(f"Handicap {i} ratio {ratio}")
                        if ratio<= 0.995:
                            found.append((f"Handicap_{s1name}_+_{s2name}_-_{i}",ratio))
                    except : 
                        pass
                try : 
                    ratio = 1/site1["1_0"]+1/site2["2_0"]
                    if ratio<= 1.015:
                        print(f"OU {i} ratio {ratio}")
                    if ratio<= 0.995:
                        found.append((f"Handicap_{s1name}_+_{s2name}_-_{i}",ratio))
                except : 
                    pass
    return found
def compute_inverse_sum(selected_keys, dict1, dict2):
    total = 0
    for key in dict1.keys():
        if key in selected_keys:
            total += 1 / dict1[key]
        else:
            total += 1 / dict2[key]
    return total
def treat_HalfTime_FullTime(sites):
    keys = list(sites[0][0].keys())  # Both dicts have the same keys
    n = len(keys)
    
    found = []
    
    # Generate all possible ways to split the keys between the two dicts
    for r in range(n + 1):
        for subset in combinations(keys, r):
            subset = set(subset)
            for site1,s1name in sites:
                for site2,s2name in sites:
                    if s2name!=s1name:
                        inverse_sum = compute_inverse_sum(subset, site1, site2)
                        if inverse_sum <= 0.99:
                            found.append((f"from {s1name}: {subset}, rest from {s2name}", inverse_sum))
    
    return found
def clean_string(s):
    return re.sub(r'AC|FC|AS|\s|-', '', s).lower().replace(" ", "")

def fetch_matches(fetch_func, name, queue):
    start = time.time()
    queue.put({name: fetch_func()})
    end = time.time()
    print(f"{name} exec time : {end-start}")


def setup_driver_binary(process_name):
    driver_path = f'C:/Users/okoone/.cache/selenium/chromedriver/win64/134.0.6998.35/chrome_driver_{process_name}.exe'
    return driver_path



def fetch_all_bets(common, name, queue,func):   
    start = time.time()
    queue.put({name: func(common,blank)})
    end = time.time()
    print(f"{name} exec time : {end-start}")

blank = {'OU':{},'WLD':{},'BTTS':{}}



if __name__ == "__main__":
    print("Import done")
    start1 = time.time()

    common=[]
    queue = Queue()
    threads = [
        threading.Thread(target=fetch_matches, args=(get_matches_188, "teams188", queue)),
        threading.Thread(target=fetch_matches, args=(get_matches_pinnacle, "teamsPinnacle", queue)),
        threading.Thread(target=fetch_matches, args=(get_matches_1xbet, "teams1xbet", queue)),
        threading.Thread(target=fetch_matches, args=(get_matches_ivi, "teamsIvi", queue)),
        threading.Thread(target=fetch_matches, args=(get_matches_mega, "teamsMega", queue)),
    ]

    for t in threads:
        t.start()
        time.sleep(1)

    for t in threads:
        t.join()

    results = {}
    while not queue.empty():
        results.update(queue.get())

    teamsPinnacle = results.get("teamsPinnacle")
    teams188 = results.get("teams188")
    teams1xbet = results.get("teams1xbet")
    teamsIvi = results.get("teamsIvi")
    teamsMega = results.get("teamsMega")

    end = time.time()
    print(f"total exec time = {end-start1}")

    # Example usage:
    teams_list = [teams188, teams1xbet, teamsPinnacle,teamsIvi,teamsMega]
    for l in teams_list:
        print(len(l))
    tdict= [{} for _ in teams_list]
    all_teams = set([])
    for it,teams in enumerate(teams_list):
        for team in teams:
            if team[0]!="Home":
                if clean_string(team[0])>clean_string(team[1]):
                    tdict[it][clean_string(team[0])+clean_string(team[1])]=team
                    all_teams.add(clean_string(team[0])+clean_string(team[1])) 
                else:
                    tdict[it][clean_string(team[1])+clean_string(team[0])]=team
                    all_teams.add(clean_string(team[1])+clean_string(team[0])) 
    for team_key in all_teams:
        found = 0
        final_tuple = [-1 for _ in tdict]
        for isite,dict_team in enumerate(tdict):
            if team_key in dict_team:
                found+=1
                final_tuple[isite] = dict_team[team_key]
        if found>=2 : 
            common.append(tuple(final_tuple))
        # else : 
        #     print(f"Team {team_key} found in {found} lists")

    # common= common[:10]

    print("!!!COMMON!!!")
    for c in common: 
        print(c)
    print("!!!COMMON!!!")
    start2 = time.time()

    

    # queue = multiprocessing.Queue()  # Use a multiprocessing Queue

    threads = [
        threading.Thread(target=fetch_all_bets, args=([c for a,b,c,d,e in common], "betsPinnacle", queue,get_all_bets_Pinnacle)),
        threading.Thread(target=fetch_all_bets, args=([a for a,b,c,d,e in common], "bets188", queue, get_all_bets_188)),
        threading.Thread(target=fetch_all_bets, args=([b for a,b,c,d,e in common], "bets1x", queue,get_all_bets_1xbet)),
        threading.Thread(target=fetch_all_bets, args=([d for a,b,c,d,e in common], "betsIvi", queue,get_all_bets_Ivi)),
        threading.Thread(target=fetch_all_bets, args=([e for a,b,c,d,e in common], "betsMega", queue,get_all_bets_Mega)),
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    results = {}
    while not queue.empty():
        results.update(queue.get())

    sPinnacle = results.get("betsPinnacle")
    s188 = results.get("bets188")
    s1x = results.get("bets1x")
    sIvi = results.get("betsIvi")
    sMega = results.get("betsMega")
            

    end = time.time()
    print(f"total exec time = {end-start1}")
    print(f"last part exec time = {end-start2}")



    arbitrage = []

    for s1x_odds,s188_odds,sPinnacle_odds,sIvi_odds,sMega_odds,common_match in zip(s1x,s188,sPinnacle,sIvi,sMega,common):
        print("--------------------------------------------------")
        print(common_match)
        valid_sites = [(site,sname) for site,sname in 
                       [(s1x_odds,"1xbet"),
                        (s188_odds,"188bet"),
                        (sPinnacle_odds,'Pinnacle'),
                         (sIvi_odds,"Ivi"),
                        (sMega_odds,"Mega")]
                        if site!={} ]
        
        for type,func in [('OU',treat_OverUnder),('WLD',treat_WLD),('BTTS',treat_BTTS),('Handicap',treat_OverUnder)]:
            arbitrage=arbitrage+func([(site[type],sname) for site,sname in valid_sites if type in site.keys()])
    for s1x_odds,s188_odds,sPinnacle_odds,sIvi_odds,sMega_odds,common_match in zip(s1x,s188,sPinnacle,sIvi,sMega,common):
        print("--------------------------------------------------")
        print(common_match)
        valid_sites = [(site,sname) for site,sname in 
                       [(s1x_odds,"1xbet"),
                        (s188_odds,"188bet"),
                        (sPinnacle_odds,'Pinnacle'),
                         (sIvi_odds,"Ivi"),
                        (sMega_odds,"Mega")]
                        if site!={} ]
        sitesHandicap = [(site['Handicap'],sname) for site,sname in valid_sites if 'Handicap' in site.keys()]
        sitesWLD=  [(site['WLD'],sname) for site,sname in valid_sites if 'WLD' in site.keys()]
        arbitrage=arbitrage+treat_Handicap_WLD(sitesHandicap,sitesWLD)

        print("-------------------------------------------------")
    print(arbitrage)

    