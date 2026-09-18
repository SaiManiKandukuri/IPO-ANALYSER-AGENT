import requests
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
import re

def clean_html(raw_html):
    if not raw_html: return ""
    return BeautifulSoup(raw_html, "html.parser").text.strip()

def main():
    now = datetime.now()
    year = now.year
    month = now.month
    fy = f'{year}-{str(year+1)[-2:]}' if month >= 4 else f'{year-1}-{str(year)[-2:]}'
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Fetch Data
    gmp_url = f'https://webnodejs.investorgain.com/cloud/v2/report/data-read/331/1/{month}/{year}/{fy}/0/all'
    sub_url = f'https://webnodejs.investorgain.com/cloud/v2/report/data-read/333/1/{month}/{year}/{fy}/0/all'
    
    gmp_data = requests.get(gmp_url, headers=headers).json().get('reportTableData', [])
    sub_data = requests.get(sub_url, headers=headers).json().get('reportTableData', [])
    
    # Convert to DataFrames
    df_gmp = pd.DataFrame(gmp_data)
    df_sub = pd.DataFrame(sub_data)
    
    # Merge on ~id
    if not df_gmp.empty and not df_sub.empty:
        df_merged = pd.merge(df_gmp, df_sub, on='~id', how='outer', suffixes=('_gmp', '_sub'))
    else:
        print("No data found")
        return
        
    print(f"Total merged IPOs: {len(df_merged)}")
    
    # Check SS Retail
    ss_retail = df_merged[df_merged['~ipo_name'] == 'SS Retail']
    if not ss_retail.empty:
        print("SS Retail GMP raw:", ss_retail.iloc[0].get('GMP'))
        print("SS Retail RII raw:", ss_retail.iloc[0].get('RII'))
        
if __name__ == '__main__':
    main()
