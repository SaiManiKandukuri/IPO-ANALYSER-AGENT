import requests
import pandas as pd
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
import sqlite3
import os

def clean_num(val):
    if pd.isna(val) or not val or str(val).strip() == '-' or str(val).strip() == '':
        return 0.0
    try:
        if isinstance(val, str):
            val = str(val).split('<br>')[0]
            val = BeautifulSoup(str(val), 'html.parser').text
            match = re.search(r'[\d\.]+', val.replace(',', ''))
            if match:
                return float(match.group())
        return float(val)
    except:
        return 0.0

def main():
    now = datetime.now()
    year = now.year
    month = now.month
    # Investorgain API format for financial year
    fy = f'{year}-{str(year+1)[-2:]}' if month >= 4 else f'{year-1}-{str(year)[-2:]}'
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    # API Endpoints that return the FULL table (bypassing DataTables pagination and limits)
    # 331 is GMP report, 333 is Subscription report
    gmp_url = f'https://webnodejs.investorgain.com/cloud/v2/report/data-read/331/1/{month}/{year}/{fy}/0/all'
    sub_url = f'https://webnodejs.investorgain.com/cloud/v2/report/data-read/333/1/{month}/{year}/{fy}/0/all'
    
    try:
        gmp_resp = requests.get(gmp_url, headers=headers)
        sub_resp = requests.get(sub_url, headers=headers)
        
        gmp_data = gmp_resp.json().get('reportTableData', [])
        sub_data = sub_resp.json().get('reportTableData', [])
    except Exception as e:
        print(f"Failed to fetch data from API: {e}")
        return

    df_gmp = pd.DataFrame(gmp_data)
    df_sub = pd.DataFrame(sub_data)
    
    if df_gmp.empty and df_sub.empty:
        print("No IPO data found for current period.")
        return
        
    # Merge both datasets on the unique IPO ID (~id)
    if not df_gmp.empty and not df_sub.empty:
        df_merged = pd.merge(df_gmp, df_sub, on='~id', how='outer', suffixes=('_gmp', '_sub'))
    elif not df_gmp.empty:
        df_merged = df_gmp
    else:
        df_merged = df_sub

    results = []
    today_str = now.strftime('%Y-%m-%d')
    
    for index, row in df_merged.iterrows():
        # The API returns both Mainboard and SME IPOs. Filter out SME IPOs based on category fields.
        cat1 = str(row.get('~ipo_category1', '')).upper()
        cat2 = str(row.get('~IPO_Category', '')).upper()
        if 'SME' in cat1 or 'SME' in cat2:
            continue
            
        # Get clean company name
        comp = row.get('~ipo_name')
        if not comp or pd.isna(comp):
            name_html = row.get('Name_gmp') or row.get('Name_sub') or row.get('Name')
            if name_html:
                soup = BeautifulSoup(str(name_html), 'html.parser')
                a_tag = soup.find('a')
                comp = a_tag.text.strip() if a_tag else BeautifulSoup(str(name_html), 'html.parser').text.strip()
            else:
                comp = "Unknown"
                
        comp = re.sub(r'(?i)\s+IPO$', '', comp)
                
        # Parse Subscriptions
        rii = clean_num(row.get('RII', 0))
        qib = clean_num(row.get('QIB', 0))
        nii = clean_num(row.get('NII', 0))
        total_sub = clean_num(row.get('Total', 0))
        
        # Parse Dates
        open_date = str(row.get('~Srt_Open', ''))
        close_date = str(row.get('~Srt_Close', ''))
        
        # Parse GMP and Price
        gmp_html = str(row.get('GMP_gmp') or row.get('GMP', ''))
        gmp = 0.0
        soup = BeautifulSoup(gmp_html, 'html.parser')
        b_tag = soup.find('b')
        if b_tag:
            gmp_text = b_tag.text.strip()
            if gmp_text and gmp_text != '--' and gmp_text != '-':
                match = re.search(r'[\d\.]+', gmp_text)
                if match:
                    gmp = float(match.group())
        
        expected_gain = clean_num(row.get('~gmp_percent_calc', 0))
        
        price_band = str(row.get('Price (\u20b9)') or row.get('IPO Price') or '-')
        if pd.isna(price_band) or price_band == 'nan':
            price_band = '-'
            
        issue_size = clean_num(row.get('IPO Size_gmp') or row.get('IPO Size_sub') or row.get('IPO Size', 0))
        
        # Bidding Status
        close_date_str = str(row.get('~Srt_Close', ''))
        if close_date_str and close_date_str != 'nan':
            bidding_status = 'Closed' if close_date_str < today_str else 'Open/Upcoming'
        else:
            bidding_status = 'Open/Upcoming'
            
        # Composite Score & Verdict Algorithm
        price_val = clean_num(price_band.split('-')[-1]) if '-' in price_band else clean_num(price_band)
        
        # Recalculate expected gain fallback if not provided by API
        if expected_gain == 0 and price_val > 0:
            expected_gain = (gmp / price_val * 100)
            
        composite_score = expected_gain * (1 + min(total_sub, 50) / 20)
        
        verdict = 'Avoid / Skip'
        if expected_gain >= 20 and (qib > 2 or rii > 2):
            verdict = 'High Conviction Apply'
        elif expected_gain > 15:
            verdict = 'Speculative / Risky'
        elif expected_gain <= 0 or (issue_size > 1000 and total_sub < 1):
            verdict = 'Avoid / Skip'
            
        results.append({
            'Company': comp,
            'Open_Date': open_date if open_date != 'nan' else '-',
            'Close_Date': close_date if close_date != 'nan' else '-',
            'Price_Band': price_band,
            'GMP': gmp,
            'Expected_Gain_Pct': round(expected_gain, 2),
            'Issue_Size_Cr': issue_size,
            'Retail_Sub': rii,
            'QIB_Sub': qib,
            'NII_Sub': nii,
            'Total_Sub': total_sub,
            'Bidding_Status': bidding_status,
            'Verdict': verdict,
            'Composite_Score': round(composite_score, 2),
            'Run_Timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
        })

    # Sort by Open Date then Close Date (latest first)
    results.sort(key=lambda x: (x['Open_Date'], x['Close_Date']), reverse=True)
    
    # Dump to JSON file
    # Output to the parent directory (root deliverables)
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ipo_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    # Store in SQLite database
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ipo_data.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ipo_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Company TEXT,
        Open_Date TEXT,
        Close_Date TEXT,
        Price_Band TEXT,
        GMP REAL,
        Expected_Gain_Pct REAL,
        Issue_Size_Cr REAL,
        Retail_Sub REAL,
        QIB_Sub REAL,
        NII_Sub REAL,
        Total_Sub REAL,
        Bidding_Status TEXT,
        Verdict TEXT,
        Composite_Score REAL,
        Run_Timestamp TEXT
    )
    ''')
    
    for r in results:
        cursor.execute('''
        INSERT INTO ipo_analysis (
            Company, Open_Date, Close_Date, Price_Band, GMP, Expected_Gain_Pct, Issue_Size_Cr,
            Retail_Sub, QIB_Sub, NII_Sub, Total_Sub, Bidding_Status,
            Verdict, Composite_Score, Run_Timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            r['Company'], r['Open_Date'], r['Close_Date'], str(r['Price_Band']), r['GMP'], r['Expected_Gain_Pct'], r['Issue_Size_Cr'],
            r['Retail_Sub'], r['QIB_Sub'], r['NII_Sub'], r['Total_Sub'], r['Bidding_Status'],
            r['Verdict'], r['Composite_Score'], r['Run_Timestamp']
        ))
        
    conn.commit()
    conn.close()
    
    print(f"Successfully scraped and stored {len(results)} IPO records!")
    # print(json.dumps(results[:2], indent=4)) # Print sample for sanity check

if __name__ == '__main__':
    main()
