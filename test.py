import time
from itertools import combinations
import threading
from queue import Queue
import pandas as pd
  # Headless mode to run without UI
import re
from test1 import *
from test2 import *
from scrapper_pinnacle import *
from scrapper_ivi import *
from scrapper_megaparis import *
from scrapper_betsson import *
from global_func import *

blank = {'OU':{},'WLD':{},'BTTS':{}}

def treat_BTTS(sites):
    found=[]
    for bet in ["","1st_Half_"]:
        for site1,s1name in sites:
            for site2,s2name in sites:
                if s2name!=s1name:
                    try :
                        ratio = 1/site1[bet+"Yes"]+1/site2[bet+"No"]
                        if ratio<= 1.01:
                            print(f"YN {ratio} {s1name}_Yes_{site1[bet+"Yes"]}_{s2name}_No_{site2[bet+"No"]} ")
                        if ratio<= 0.999:
                            found.append((f"{s1name}_Yes_{site1[bet+"Yes"]}_{s2name}_No_{site2[bet+"No"]}_{bet}",ratio))
                    except: 
                        pass
    return found
def treat_WLD(sites):
    found = []
    all_ratios = []

    for bet in ["", "1st_Half_"]:
        for site1, s1name in sites:
            for site2, s2name in sites: 
                for site3, s3name in sites:
                    if not (s2name == s1name and s2name == s3name):
                        try:
                            ratio = 1 / site1[bet + "1"] + 1 / site2[bet + "X"] + 1 / site3[bet + "2"]
                            all_ratios.append(ratio)

                            if ratio <= 1.01:
                                print(f"WLD ratio {s1name}_1_{s2name}_X_{s3name}_2_{bet} {ratio:.6f} {site1[bet+'1']}_{site2[bet+'X']}_{site3[bet+'2']}")
                            if ratio <= 0.999:
                                found.append((f"{s1name}_1_{s2name}_X_{s3name}_2_{bet}", ratio))
                        except:
                            pass

    if all_ratios:
        print(f"MIN RATIO : {min(all_ratios):.6f} , {sites}")
    else:
        print(f"NO RATIO : {sites}")

    return list(set(found))

def treat_Handicap_WLD(sitesHandicap,sitesWLD):
    found = []
    for oddsHandicap,sname1 in sitesHandicap:
        if oddsHandicap!={}:
           
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
                                    if ratio<= 1.01:
                                        print(f"Handi {hdTeam} WLD ratio {sname1}_1_{o1}_handi0_{sname2}_X_{draw}_{sname3}_2_{w2} {ratio}")
                                    if ratio<= 0.999:
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
                                    if ratio<= 1.01:
                                        print(f"Handi {hdTeam} WLD ratio {sname1}_1_{o1}_handi0_{sname2}_X_{draw}_{sname3}_2_{w2} {ratio}")
                                    if ratio<= 0.999:
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
                                    if ratio<= 1.01:
                                        print(f"Handi {hdTeam} WLD ratio {sname1}_1_{o1}_handi0_{sname2}_X_{draw}_{sname3}_2_{w2} {ratio}")
                                    if ratio<= 0.999:
                                        found.append((f"{sname1}_1_{sname2}_X_{sname3}_2",ratio))
                                except :
                                    pass
                            except:
                                pass

    return found

def treat_OverUnder(sites):
    found=[]
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
                for i in ["0.25","0.75","0.5","1","1.25","1.5","1.75","2","2.25","2.5","2.75"]:
                    try : 
                        ratio = 1/site1["1_+"+i]+1/site2["2_-"+i]
                        if ratio<= 1.01:
                            print(f"{ratio} Handicap_{s1name}_+_{s2name}_-_{i} {site1["1_+"+i]}_{site2["2_-"+i]}")
                        if ratio<= 0.999:
                            found.append((f"Handicap_{s1name}_+_{s2name}_-_{i}",ratio))
                    except : 
                        pass
                try : 
                    ratio = 1/site1["1_0"]+1/site2["2_0"]
                    if ratio<= 1.01:
                        print(f"{ratio} Handicap_{s1name}_+_{s2name}_-_0 {site1["1_0"]} {site2["2_0"]}")
                    if ratio<= 0.999:
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


def fetch_matches(fetch_func, name, queue):
    start = time.time()
    queue.put({name: fetch_func()})
    end = time.time()
    print(f"{name} exec time : {end-start}")

def fetch_all_bets(common, name, queue,func):   
    start = time.time()
    queue.put({name: func(common,blank)})
    end = time.time()
    print(f"{name} exec time : {end-start}")


def process_odds_to_find_arbs(sites,snames=["1xbet","188bet","Pinnacle","Ivi","Mega"]):
    arbitrage = []
    print("--------------------------------------------------")
    valid_sites = [(site,sname) for site,sname in zip(sites,snames) if site!={} ]
    
    for type,func in [('OU',treat_OverUnder),('WLD',treat_WLD),('BTTS',treat_BTTS),('Handicap',treat_OverUnder)]:
        vld_sites= [(site[type],sname) for site,sname in valid_sites if type in site.keys()]
        arbitrage=arbitrage+func([(site,sname) for site,sname in vld_sites if site != {}])

    sitesHandicap = [(site['Handicap'],sname) for site,sname in valid_sites if 'Handicap' in site.keys()]
    sitesWLD=  [(site['WLD'],sname) for site,sname in valid_sites if 'WLD' in site.keys()]
    siteWLD_Not_Empty = [(site,sname) for site,sname in sitesWLD if site != {}]
    arbitrage=arbitrage+treat_Handicap_WLD(sitesHandicap,siteWLD_Not_Empty)
    print("-------------------------------------------------")
    print(arbitrage)


def process_as_it_comes(queue,snames):
    while True: 
        try:
            qres=queue.get()
            common,odds = qres
        except Exception as e:
            print(f"queue pb : {qres}  ERROR : {e}")
        if odds ==[]:
            break
        else : 
            print(common)
            process_odds_to_find_arbs(odds,snames)

def odds_requester(commons,queues_in,queues_out,odd_processor_queue):
    for c,common in enumerate(commons):
        all_odds= []
        for site,queue in zip(list(common),queues_in):
            queue.put(site)
        print(c)
        for queue in queues_out:   
            all_odds.append(queue.get())
        odd_processor_queue.put((common,all_odds))
        
    for queue in queues_in :
        queue.put(0,[])
    odd_processor_queue.put(0,[])
    print('HERE')

if __name__ == "__main__":
    print("Import done")
    start1 = time.time()

    common=[]
    queue = Queue()
    snames=["1xbet","188bet","Pinnacle","Ivi","Mega","betsson"] 
    threads = [
        threading.Thread(target=fetch_matches, args=(get_matches_188, "teams188", queue)),
        threading.Thread(target=fetch_matches, args=(get_matches_pinnacle, "teamsPinnacle", queue)),
        threading.Thread(target=fetch_matches, args=(get_matches_1xbet, "teams1xbet", queue)),
        threading.Thread(target=fetch_matches, args=(get_matches_ivi, "teamsIvi", queue)),
        threading.Thread(target=fetch_matches, args=(get_matches_mega, "teamsMega", queue)),
        threading.Thread(target=fetch_matches, args=(get_matches_betsson, "betsson", queue)),
    ]

    for t in threads:
        t.start()

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
    teamsBetsson = results.get("betsson")


    end = time.time()
    print(f"total exec time = {end-start1}")
    
    # Example usage:
    teams_list = [teams1xbet,teams188, teamsPinnacle,teamsIvi,teamsMega,teamsBetsson]

    notFound=[]
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
        else : 
            notFound.append(tuple(final_tuple))

    all_not = {n:[] for n in snames}
    for tuple in common : 
        for t,val in enumerate(list(tuple)):
            if val!=-1:
                all_not[snames[t]].append((list(val)[0],list(val)[1]))
            else :
                all_not[snames[t]].append(("",""))
    for tuple in notFound : 
        for t,val in enumerate(list(tuple)):
            if val!=-1:
                all_not[snames[t]].append((list(val)[0],list(val)[1]))
            else :
                all_not[snames[t]].append(("",""))
                
    df = pd.DataFrame(all_not)
    # Save to Excel file
    df.to_excel("teams_data.xlsx", index=False)
    
    
    for c in common: 
        print(c)
    print("!!!COMMON!!!")
    print(f'Total : {len(common)}')
    
    start2 = time.time()
    
    sfunctions=[get_all_bets_threader_1xbet,get_all_bets_threader_188,get_all_bets_threader_Pinnacle,get_all_bets_threader_Ivi,get_all_bets_threader_Mega,get_all_bets_threader_Betsson]
    queues_in = [Queue() for _ in snames]
    queues_out = [Queue() for _ in snames]
    queues_in2 = [Queue() for _ in snames]
    queues_out2 = [Queue() for _ in snames]
    threads = [threading.Thread(target=sfunc, args=(queue_in,queue_out,blank)) for sfunc,queue_in,queue_out in zip(sfunctions,queues_in,queues_out)]+[threading.Thread(target=sfunc, args=(queue_in,queue_out,blank)) for sfunc,queue_in,queue_out in zip(sfunctions,queues_in2,queues_out2)]

    odds_processer_queue= Queue()
    mid = len(common) // 2
    threads.append(threading.Thread(target=odds_requester, args=(common[:mid],queues_in,queues_out,odds_processer_queue)))
    threads.append(threading.Thread(target=odds_requester, args=(common[mid:],queues_in2,queues_out2,odds_processer_queue)))
    threads.append(threading.Thread(target=process_as_it_comes, args=(odds_processer_queue,snames)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    end = time.time()
    print(f"total exec time = {end-start1}")
    print(f"last part exec time = {end-start2}")


    

    