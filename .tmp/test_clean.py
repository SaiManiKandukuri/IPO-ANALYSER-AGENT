import re
from bs4 import BeautifulSoup

def clean_num(val):
    if not val or str(val).strip() == '-' or str(val).strip() == '':
        return 0.0
    try:
        if isinstance(val, str):
            val = str(val).split('<br>')[0]  # Split before parsing HTML
            val = BeautifulSoup(val, 'html.parser').text
            match = re.search(r'[\d\.]+', val.replace(',', ''))
            if match:
                return float(match.group())
        return float(val)
    except:
        return 0.0

print(clean_num('<b>107.41</b><br><small style="font-size: 12px; color: #007BFF;""><b>18th Sep 18:56</b></small>'))
