import re
from unidecode import unidecode
DISPLAY_CONNECTION_ERROR = False
def logwrite(message,display_type=""):
    if display_type == "CONNECTION_ERROR" and DISPLAY_CONNECTION_ERROR:
        print(message)
    if display_type == "":
        print(message)
MAPPING_MATCH = {
    "man city": "manchester city",
    "manchester united": "man utd",
    "bayern munich": "bayern",
    "psg": "paris saint-germain",
    "inter milan": "inter",
    "real madrid": "real",
    "barça": "barcelona",
    "juventus": "juve",
    "spurs": "tottenham",
    "olympique de marseille": "marseille",
    "olympique lyonnais": "lyon",
    "olympique lyon": "lyon"
    "rodez aveyron football": "rodez",
}

TRANSFORM_MAPPING = {
    "u19":"under ages",
    "u20":"under age",
    "u21":"und age",
    "u23":"under a",
    "warsawa": "warsaw",
    "milano": "milan",
    "sevilla": "seville",
    "torino": "turin",
    "fluminense": "flu",
    "botafogo": "bota",
    "internacional": "inter",
    "internazional": "inter",
    "cruzeiro": "cruz",
    "fortaleza": "forta",
    "bahia": "bah",
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
    s = re.sub(r'\b\w{1,2,3}\b', '', s)
    s = re.sub(r'Borussia|stade|club|\s|city|town|county|united|-|\b\d+\.\b|\d+', '', s)
    # s = re.sub(r'us |afc|ac|nk|fc|as|vfl|vfb|sm|ca|Borussia|rc|stade|club|\s|city|town|sl|cp|county|united|fsv|tsg|rb|and|&|-|\b\d+\.\b|\d+| i | ii ', '', s)
    #removes every part smaller than 2 chars
    

    # Remove spaces
    return s.replace(" ", "")