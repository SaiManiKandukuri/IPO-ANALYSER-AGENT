import re
from bs4 import BeautifulSoup

def clean_num(val):
    if not val or str(val).strip() == '-' or str(val).strip() == '':
        return 0.0
    try:
        if isinstance(val, str):
            val = BeautifulSoup(str(val), 'html.parser').text
            match = re.search(r'[\d\.]+', val.replace(',', ''))
            if match:
                return float(match.group())
        return float(val)
    except:
        return 0.0

print(clean_num('<b>0.62</b><br>'))
print(clean_num('&#8377;405.00 Cr'))
print(clean_num('405'))
print(clean_num('-'))
print(clean_num('35.81'))
