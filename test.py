import time
from itertools import combinations
import threading
from queue import Queue
import pandas as pd
import math
# from test1 import *
from scrapper_1xbet import *
from scrapper_pinnacle import *
from scrapper_ivi import *
# from scrapper_megaparis import *
# from scrapper_betsson import *
from global_func import *

blank = {'OU':{},'WLD':{},'BTTS':{}}

def treat_BTTS(sites):
    found=[]
    for bet in ["","1st_Half_"]:
        for site1,sname1 in sites:
            for site2,sname2 in sites:
                if sname2!=sname1:
                    try :
                        ratio = 1/site1[bet+"Yes"]+1/site2[bet+"No"]
                        if ratio<= 1.005:
                            print(f"YN {ratio} {sname1}_Yes_{site1[bet+'Yes']}_{sname2}_No_{site2[bet+'No']} ")
                        if ratio<= 0.995:
                            found.append((f"{sname1}_Yes_{site1[bet+'Yes']}_{sname2}_No_{site2[bet+'No']}_{bet}",ratio))
                    except: 
                        pass
    return found

def treat_WLD_DoubleChance(sitesWLD,sitesDoubleChance):
    found = []
    for site1, sname1 in sitesDoubleChance:
        for site2, sname2 in sitesWLD: 
            if not sname2 == sname1 :
                for s1bet,s2bet in [('1X','2'),('12','X'),('2X','1')]:
                    try : 
                        o1,o2=site1[s1bet],site2[s2bet]
                        s1,s2 = 1/o1, 1/o2
                        ratio = s2+ s1
                        stake1,stake2 = round (s1*200, 0),round (s2*200, 0)
                        minGain = min(stake1*o1, stake2*o2)/(stake1+stake2)
                        if ratio<= 1.005:
                                print(f"DoubleChance {sname1}:{s1bet}:{o1} {sname2}:{s2bet}:{o2} {ratio:.6f}")
                        if (minGain >= 1.000 or ratio<= 0.996)  and ratio>= 0.75:
                            found.append((f"DoubleChance {sname1}:{s1bet}:{o1} {sname2}:{s2bet}:{o2} {ratio:.6f}  \n"
                                            f"Bet {sname1}:{s1bet}:{stake1} {sname2}:{s2bet}:{stake2}  min gain {minGain}\n"
                                            , ratio))
                    except : 
                        pass
    return list(set(found))

def treat_WLD(sites):
    found = []
    all_ratios = []

    
    for site1, sname1 in sites:
        for site2, sname2 in sites: 
            for site3, sname3 in sites:
                if not (sname2 == sname1 and sname2 == sname3 and sname1 == sname3):
                    try:
                        o1 = site1["1"]
                        o2 = site2["X"]
                        o3 = site3["2"]
                        s1 = 1/o1
                        s2 = 1/o2
                        s3 = 1/o3

                        ratio = s1 + s2 + s3
                        all_ratios.append(ratio)

                        stake1,stake2,stake3 = round (s1*200, 0),round (s2*200, 0),round (s3*200, 0)
                        minGain = min(stake1*o1, stake2*o2, stake3*o3)/(stake1+stake2+stake3)

                        if ratio<= 1.005:
                            print(f"WLD ratio {sname1}:1:{o1} {sname2}:X:{o2} {sname3}:2:{o3} {ratio:.6f}")
                        if (minGain >= 1.000 or ratio<= 0.996)  and ratio>= 0.75:
                            found.append((f"WLD ratio {sname1}:1:{o1} {sname2}:X:{o2} {sname3}:2:{o3} {ratio:.6f}  \n"
                                            f"Bet {sname1}:1:{stake1} {sname2}:X:{stake2} {sname3}:2:{stake3} min gain {minGain}\n"
                                            , ratio))
                    except:
                        pass
    if all_ratios:
        if min(all_ratios)<1.015 and min(all_ratios)>1.007:
            print(f"MIN RATIO : {min(all_ratios):.6f} , {sites}")
    else:
        print(f"NO RATIO : {sites}")

    return list(set(found))



Handicap_WLD_Configs=[
{
    'bet1_bet2_list' : [("1_0","2"),("2_0","1")],
    "stake2": lambda o1, o2: (o1 - 1) / (o1 * o2),
    'gain' : lambda o1,o2,o3,stake1,stake2,stake3 : min(stake1*o1, stake2*o2 + stake1, stake3*o3)/(stake1+stake2+stake3)
},
{
    'bet1_bet2_list' : [("1_+0.25","2"),("2_+0.25","1")],
    "stake2": lambda o1, o2: (o1 - 1) / (o1 * o2),
    'gain' : lambda o1,o2,o3,stake1,stake2,stake3 : min(stake1*o1, stake2*o2 + stake1, stake3*o3)/(stake1+stake2+stake3)
},

]




def treat_Handicap_WLD(sitesHandicap,sitesWLD):
    found = []
    for oddsHandicap,sname1 in sitesHandicap:
        if oddsHandicap!={}:
           
            for site2,sname2 in sitesWLD: 
                for site3,sname3 in sitesWLD: 
                    # for hdTeam,winTeam in Handicap_WLD_Configs[0]['bet1_bet2_list']:
                    #     if not (sname2==sname1 and sname2==sname3):
                    #             try:
                    #                 o1,o2,o3 = oddsHandicap[hdTeam],site2["X"],site3[winTeam]
                    #             except : 
                    #                 print(sname1)
                    #                 print(oddsHandicap)
                    #             s1,s2,s3 = 1/o1, Handicap_WLD_Configs[0]['stake2'](o1,o2), 1/o3
                    #             ratio = s1+ s2+s3
                    #             stake1,stake2,stake3 = round (s1*200, 0),round (s2*200, 0),round (s3*200, 0)
                    #             minGain = Handicap_WLD_Configs[0]['gain'](o1,o2,o3,stake1,stake2,stake3)
                    #             if ratio<= 1.005:
                    #                 print(f"Handi {hdTeam} WLD ratio {sname1}_1_{o1}_handi_{sname2}_X_{draw}_{sname3}_2_{w2} {ratio}")
                    #             if (minGain >= 1.000 or ratio<= 0.996)  and ratio>= 0.75:
                    #                 found.append((f"Handi {sname1}:{hdTeam}:{o1} {sname2}:X:{draw} {sname3}:{winTeam}:{w2} {ratio:.6f}  \n"
                    #                         f"Bet {sname1}:{hdTeam}:{stake1} {sname2}:X:{stake2} {sname3}:{winTeam}:{stake3} min gain {minGain}\n"
                    #                         , ratio))
                            


                    for hdTeam,winTeam in [("1_0","2"),("2_0","1")]:
                        if not (sname2==sname1 and sname2==sname3):
                            try:
                                o1 = oddsHandicap[hdTeam]
                                draw = site2["X"]
                                w2 = site3[winTeam]
                                s1 = 1/o1
                                s2 = (o1-1)/(o1*draw)
                                s3 = 1/w2
                                
                                ratio = s1+ s2+s3
                                stake1,stake2,stake3 = round (s1*200, 0),round (s2*200, 0),round (s3*200, 0)

                                minGain = min(stake1*o1, stake2*draw + stake1, stake3*w2)/(stake1+stake2+stake3)
                                if ratio<= 1.005:
                                    print(f"Handi {hdTeam} WLD ratio {sname1}_1_{o1}_handi0_{sname2}_X_{draw}_{sname3}_2_{w2} {ratio}")
                                if (minGain >= 1.000 or ratio<= 0.996)  and ratio>= 0.75:
                                    found.append((f"Handi {sname1}:{hdTeam}:{o1} {sname2}:X:{draw} {sname3}:{winTeam}:{w2} {ratio:.6f}  \n"
                                            f"Bet {sname1}:{hdTeam}:{stake1} {sname2}:X:{stake2} {sname3}:{winTeam}:{stake3} min gain {minGain}\n"
                                            , ratio))
                            except Exception as e:
                                pass
                                
                                
                    

                    for hdTeam,winTeam in [("1_+0.25","2"),("2_+0.25","1")]:
                        if not (sname2==sname1 and sname2==sname3):
                            try:
                                o1 = oddsHandicap[hdTeam]
                                draw = site2["X"]
                                w2 = site3[winTeam]
                                s1 = 1/o1
                                s2 = 1/(2*draw)
                                s3 = 1/w2
                                try : 
                                    ratio = s1+ s2+s3
                                    stake1,stake2,stake3 = round (s1*200, 0),round (s2*200, 0),round (s3*200, 0)
                                    minGain = min(stake1*o1, stake2*draw + 0.5*stake1*o1, stake3*w2)/(stake1+stake2+stake3)
                                    if ratio<= 1.005:
                                        print(f"Handi {hdTeam} WLD ratio {sname1}_1_{o1}_handi0_{sname2}_X_{draw}_{sname3}_2_{w2} {ratio}")
                                    if (minGain >= 1.000 or ratio<= 0.996)  and ratio>= 0.75:
                                        found.append((f"Handi {sname1}:{hdTeam}:{o1} {sname2}:X:{draw} {sname3}:{winTeam}:{w2} {ratio:.6f}  \n"
                                              f"Bet {sname1}:{hdTeam}:{stake1} {sname2}:X:{stake2} {sname3}:{winTeam}:{stake3} min gain {minGain}\n"
                                              , ratio))
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
                                s1 = 1/o1
                                s2 = (1-(1/(2*o1)))/(draw)
                                s3 = 1/w2
                                try : 
                                    ratio = s1+ s2+s3
                                    stake1,stake2,stake3 = round (s1*200, 0),round (s2*200, 0),round (s3*200, 0)
                                    minGain = min(stake1*o1, stake2*draw + 0.5*stake1, stake3*w2)/(stake1+stake2+stake3)
                                    if ratio<= 1.005:
                                        print(f"Handi {hdTeam} WLD ratio {sname1}_1_{o1}_handi0_{sname2}_X_{draw}_{sname3}_2_{w2} {ratio}")
                                    if (minGain >= 1.000 or ratio<= 0.996)  and ratio>= 0.75:
                                        found.append((f"Handi {sname1}:{hdTeam}:{o1} {sname2}:X:{draw} {sname3}:{winTeam}:{w2} {ratio:.6f}  \n"
                                              f"Bet {sname1}:{hdTeam}:{stake1} {sname2}:X:{stake2} {sname3}:{winTeam}:{stake3} min gain {minGain}\n"
                                              , ratio))
                                except :
                                    pass
                            except:
                                pass
    return found

def treat_OverUnder(sites):
    found=[]
    for site1,sname1 in sites:
        for site2,sname2 in sites:
            if sname2!=sname1:
                for i in ["0.5","1","1.5","2","2.5","3","3.5","4","4.5"]:
                    try : 
                        o1 = site1["O_"+i]
                        o2 = site2["U_"+i]
                        ratio = 1/o1+1/o2
                        stake1 = round (1/o1*150, 0)
                        stake2 = round (1/o2*150, 0)
                        minGain = min(stake1*o1, stake2*o2)/(stake1+stake2)
                        if ratio<= 1.005 and ratio>= 0.75 :
                            print(f"OU {i} ratio {ratio}")
                        if (minGain >= 1.000 or ratio<= 0.996)  and ratio>= 0.75:
                            found.append((f"OU {i} {sname1}_O_{o1} {sname2}_U_{o2} {ratio:.6f}  \n"
                                          f"Bet {sname1}_O_{stake1} {sname2}_U_{stake2} min gain {minGain}",ratio))
                    except : 
                        pass
                for i in ["0.25","0.75","0.5","1","1.25","1.5","1.75","2","2.25","2.5","2.75"]:
                    try : 
                        o1 = site1["1_+"+i]
                        o2 = site2["2_-"+i]
                        s1 = 1/o1
                        s2 = 1/o2
                        ratio = s1+s2
                        stake1 = round (s1*150, 0)
                        stake2 = round (s2*150, 0)
                        minGain = min(stake1*o1, stake2*o2)/(stake1+stake2)
                        if ratio<= 1.005 and ratio>= 0.75:
                            print(f"Handicap {i} {sname1}_+_{o1}  {sname2}_-_{o2} {ratio}")
                        if (minGain >= 1.000 or ratio<= 0.996)  and ratio>= 0.75:
                            found.append((f"Handicap {i} {sname1}_+_{o1}  {sname2}_-_{o2} {ratio} \n"
                                          f"Bets {sname1}_+_{stake1}  {sname2}_-_{stake2} min gain {minGain}",ratio))
                
                    except : 
                        pass
                try : 
                    o1 = site1["1_0"]
                    o2 = site2["2_0"]
                    ratio = 1/o1+1/o2
                    stake1 = round (1/o1*150, 0)
                    stake2 = round (1/o2*150, 0)
                    minGain = min(stake1*o1, stake2*o2)/(stake1+stake2)
                    if ratio<= 1.005:
                            print(f"Handicap 0 {sname1}_+_{o1}  {sname2}_-_{o2} {ratio}")
                    if (minGain >= 1.000 or ratio<= 0.996)  and ratio>= 0.75:
                        found.append((f"Handicap 0 {sname1}_+_{o1}  {sname2}_-_{o2} {ratio} \n"
                                        f"Bets {sname1}_+_{stake1}  {sname2}_-_{stake2} min gain {minGain}",ratio))
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
            for site1,sname1 in sites:
                for site2,sname2 in sites:
                    if sname2!=sname1:
                        inverse_sum = compute_inverse_sum(subset, site1, site2)
                        if inverse_sum <= 0.99:
                            found.append((f"from {sname1}: {subset}, rest from {sname2}", inverse_sum))
    
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
    # print("--------------------------------------------------")
    valid_sites = [(site,sname) for site,sname in zip(sites,snames) if site!={} ]
    
    for types,func in [('OU',treat_OverUnder),('WLD',treat_WLD),('BTTS',treat_BTTS),('Handicap',treat_OverUnder)]:
        try : 
            vld_sites= [(site[types],sname) for site,sname in valid_sites if types in site.keys()]
            arbitrage=arbitrage+func([(site,sname) for site,sname in vld_sites if site != {}])
        except : 
            for valid_site in valid_sites:
                print(valid_site)
        
    try : 
        sitesHandicap = [(site['Handicap'],sname) for site,sname in valid_sites if 'Handicap' in site.keys()]
        sitesWLD=  [(site['WLD'],sname) for site,sname in valid_sites if 'WLD' in site.keys()]
        sitesDoubleChance = [(site['doubleChance'],sname) for site,sname in valid_sites if 'doubleChance' in site.keys()]

        siteWLD_Not_Empty = [(site,sname) for site,sname in sitesWLD if site != {}]
        arbitrage = arbitrage+treat_Handicap_WLD(sitesHandicap,siteWLD_Not_Empty)
        arbitrage = arbitrage+treat_WLD_DoubleChance(siteWLD_Not_Empty,sitesDoubleChance)
    except :
        pass
    # print("-------------------------------------------------")
    # print(arbitrage)
    return arbitrage


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
            # try :
            arbitrages = process_odds_to_find_arbs(odds,snames)
            # except Exception as e:
            #     print(e)
            #     print(common)
            #     print (odds)
            if arbitrages != [] :
                print("-------------------------------------------------") 
                print(common)
                for arb in arbitrages:
                    txt, rat = arb
                    print(txt)
                print("-------------------------------------------------")
                

def odds_requester(commons,queues_in,queues_out,odd_processor_queue):
    for c,common in enumerate(commons):
        all_odds= []
        for site,queue in zip(list(common),queues_in):
            queue.put(site)
        if c%20==0:
            print(c)
        for queue in queues_out:   
            all_odds.append(queue.get())
        odd_processor_queue.put((common,all_odds))
        
    for queue in queues_in :
        queue.put(0)
    odd_processor_queue.put((0,[]))
    print('HERE')

if __name__ == "__main__":
    print("Import done")
    while True:
        start1 = time.time()

        common=[]
        queue = Queue()
        snames=[
                "1xbet",
                # "188bet",
                "Pinnacle",
                # "Ivi",
                # "Mega",
                # "betsson"
                ] 
        sfunctions=[
            get_all_bets_threader_1xbet,
            # get_all_bets_threader_188,
            get_all_bets_threader_Pinnacle,
            # get_all_bets_threader_Ivi,
            # get_all_bets_threader_Mega,
            # get_all_bets_threader_Betsson
            ]

        threads = [
            # threading.Thread(target=fetch_matches, args=(get_matches_188, "teams188", queue)),
            threading.Thread(target=fetch_matches, args=(get_matches_pinnacle, "teamsPinnacle", queue)),
            threading.Thread(target=fetch_matches, args=(get_matches_1xbet, "teams1xbet", queue)),
            # threading.Thread(target=fetch_matches, args=(get_matches_ivi, "teamsIvi", queue)),
            # threading.Thread(target=fetch_matches, args=(get_matches_mega, "teamsMega", queue)),
            # threading.Thread(target=fetch_matches, args=(get_matches_betsson, "betsson", queue)),
        ]
        print("getting pairs")
        for t in threads:
            t.start()

        for t in threads:
            t.join()

        results = {}
        while not queue.empty():
            results.update(queue.get())

        teamsPinnacle = results.get("teamsPinnacle")
        # teams188 = results.get("teams188")
        teams1xbet = results.get("teams1xbet")
        # teamsIvi = results.get("teamsIvi")
        # teamsMega = results.get("teamsMega")
        # teamsBetsson = results.get("betsson")


        end = time.time()
        print(f"total exec time = {end-start1}")
        
        # Example usage:
        teams_list = [
            teams1xbet,
            # teams188,
            teamsPinnacle,
            # teamsIvi,
            # teamsMega,
            # teamsBetsson
            ]

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
        for t in common : 
            for t,val in enumerate(list(t)):
                if val!=-1:
                    all_not[snames[t]].append((list(val)[0],list(val)[1]))
                else :
                    all_not[snames[t]].append(("",""))
        for t in notFound : 
            for t,val in enumerate(list(t)):
                if val!=-1:
                    all_not[snames[t]].append((list(val)[0],list(val)[1]))
                else :
                    all_not[snames[t]].append(("",""))

        df = pd.DataFrame(all_not)
        # Save to Excel file
        df.to_excel("teams_data.xlsx", index=False)
        
        
        # for c in common: 
        #     print(c)
        print("!!!COMMON!!!")
        print(f'Total : {len(common)}')
        
        start2 = time.time()
        
        # queues_in = [Queue() for _ in snames]
        # queues_out = [Queue() for _ in snames]
        # queues_in2 = [Queue() for _ in snames]
        # queues_out2 = [Queue() for _ in snames]
        # queues_in3 = [Queue() for _ in snames]
        # queues_out3 = [Queue() for _ in snames]
        division_number = 4
        all_queues = [([Queue() for _ in snames],[Queue() for _ in snames]) for _ in range(division_number)]
        threads = []
        for queues_in,queues_out in all_queues:
            threads+=[threading.Thread(target=sfunc, args=(queue_in,queue_out,blank)) for sfunc,queue_in,queue_out in zip(sfunctions,queues_in,queues_out)]

        # threads = [threading.Thread(target=sfunc, args=(queue_in,queue_out,blank)) for sfunc,queue_in,queue_out in zip(sfunctions,queues_in,queues_out)]+[threading.Thread(target=sfunc, args=(queue_in,queue_out,blank)) for sfunc,queue_in,queue_out in zip(sfunctions,queues_in2,queues_out2)]
        # threads = threads+[threading.Thread(target=sfunc, args=(queue_in,queue_out,blank)) for sfunc,queue_in,queue_out in zip(sfunctions,queues_in3,queues_out3)]
        odds_processer_queue= Queue()
        div = math.ceil(len(common) / division_number)
        for q, queues in enumerate(all_queues):
            queues_in, queues_out = queues
            start = div * q
            end = min(start + div, len(common))
            if start < len(common):  # Ensure we don't start beyond the list
                threads.append(threading.Thread(
                    target=odds_requester,
                    args=(common[start:end], queues_in, queues_out, odds_processer_queue)
                ))
        # threads.append(threading.Thread(target=odds_requester, args=(common[:mid],queues_in,queues_out,odds_processer_queue)))
        # threads.append(threading.Thread(target=odds_requester, args=(common[mid:2*mid],queues_in2,queues_out2,odds_processer_queue)))
        # threads.append(threading.Thread(target=odds_requester, args=(common[2*mid:],queues_in3,queues_out3,odds_processer_queue)))
        threads.append(threading.Thread(target=process_as_it_comes, args=(odds_processer_queue,snames)))
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        end = time.time()
        print(f"total exec time = {end-start1}")
        print(f"last part exec time = {end-start2}")


    

    