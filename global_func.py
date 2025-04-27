import re
from unidecode import unidecode
from datetime import datetime,timedelta
import os 
import webbrowser

DISPLAY_CONNECTION_ERROR = True
TIMERANGE_START = 0
TIMERANGE = 4
DIVISION_NUMBER = 1
browser_selected = "edge"

def logwrite(message,display_type=""):
    if display_type == "CONNECTION_ERROR" and DISPLAY_CONNECTION_ERROR:
        print(message)
    if display_type == "":
        print(message)

def open_chrome(url):
    if browser_selected == "chrome":
        chrome_path = 'C:/Program Files/Google/Chrome/Application/chrome.exe %s'
        webbrowser.get(chrome_path).open(url)
    elif browser_selected == "edge":
        os.system(f'start msedge {url}')



def is_within_4_days(timestamp):
    now = datetime.now()
    if type(timestamp) == str:
        cutoff_dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
    else :
        if timestamp > 100000000000:
            cutoff_dt = datetime.fromtimestamp(timestamp/1000)
        else :
            cutoff_dt = datetime.fromtimestamp(timestamp)
    return now + timedelta(days=TIMERANGE_START) <= cutoff_dt <= now + timedelta(days=TIMERANGE)

async def is_within_4_days_async(timestamp,website = "ivi"):
    now = datetime.now()
    if type(timestamp) == str:
        if website == "pinnacle":
            cutoff_dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
        elif website == "ivi":
            cutoff_dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    else :
        if timestamp > 100000000000:
            cutoff_dt = datetime.fromtimestamp(timestamp/1000)
        else :
            cutoff_dt = datetime.fromtimestamp(timestamp)
    return now + timedelta(days=TIMERANGE_START) <= cutoff_dt <= now + timedelta(days=TIMERANGE)

MAPPING_MATCH = {
    "man city": "manchester city",
    "man utd" : "manchester united",
    "bayern munich": "bayern",
    "psg": "paris saint-germain",
    "inter milan": "inter",
    "real madrid": "real",
    "barça": "barcelona",
    "juventus": "juve",
    "spurs": "tottenham",
    "olympique de marseille": "marseille",
    "olympique lyonnais": "lyon",
    "olympique lyon": "lyon",
    "rodez aveyron football": "rodez",
    "nancy-loraine": "nancy",
    'bodoe/glimt' : "bodo glimt",
    'lazio rome' : "lazio"
}

TRANSFORM_MAPPING = {
    "ii" : "deux",
    "u19":"under agea",
    "u20":"under ageb",
    "u21":"under agec",
    "u23":"under aged",
    "warsawa": "warsaw",
    "milano": "milan",
    "sevilla": "seville",
    "torino": "turin",
    "(women)":"",
    ".": "",
    # "flu": "fluminense",
    "botafogo": "bota",
    "internacional": "inter",
    "internazional": "inter",
    "cruzeiro": "cruz",
    "fortaleza": "forta",
    # "bah": "bahia",
    "paranaense": "athletico"

}
def clean_string(s):
    s = s.lower()
    for key, value in TRANSFORM_MAPPING.items():
        s = s.replace(key, value)
    # Apply pre-mapping if provided
    if MAPPING_MATCH:
        for key, value in MAPPING_MATCH.items():
            if key in s:
                s = value
                break
    
    
    # Normalize accents
    s = unidecode(s)
    # Convert to lowercase
    s = s.lower()
    # Remove unwanted patterns
    if re.sub(r'\b\w{1,3}\b', '', s) != "":
        s = re.sub(r'\b\w{1,3}\b', '', s)
    s = re.sub(r'Borussia|stade|club|\s|city|town|county|united|-|\b\d+\.\b|\d+', '', s)
    # s = re.sub(r'us |afc|ac|nk|fc|as|vfl|vfb|sm|ca|Borussia|rc|stade|club|\s|city|town|sl|cp|county|united|fsv|tsg|rb|and|&|-|\b\d+\.\b|\d+| i | ii ', '', s)
    #removes every part smaller than 2 chars
    

    # Remove spaces
    return s.replace(" ", "")

# print(clean_string('Inter Miami II'))