import re
def clean_string(s):
    # Remove unwanted patterns
    s= s.lower()
    s = re.sub(r'afc|ac|fc|as|vfl|vfb|ca|club|\s|city|town|county|united|fsv|tsg|rb|-|\b\d+\.\b|\d+| i | ii ', '', s)
    # Convert to lowercase and remove spaces
    return s.replace(" ", "")